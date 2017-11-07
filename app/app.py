from flask import Blueprint, Flask, jsonify, render_template
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
from flask_restplus import Api, fields, Resource

api_bp = Blueprint(
	"api",
	__name__,
	template_folder="templates"
)

api = Api(
	api_bp,
	title="Example Flask API",
	description="Demo some Flask features.",
	catch_all_404s=True
)

app = Flask(__name__)

app.register_blueprint(api_bp)

app.secret_key = "HU6D8bT^uP4UaUK"
jwt = JWTManager(app)

parser = api.parser()

# Simple get examples
simple_namespace = api.namespace(
	"Examples - Pt. 1",
	description="Get examples.",
	path="/"
)

@api.response(200, "OK")
@api.doc(params={"name": "A name."})
@simple_namespace.route("/hellobypath/<string:name>")
class HelloByPath(Resource):
	def get(self, name):
		"""
		Says hello

		Says hello to the name specified by path.
		"""

		request = {"name": name}

		return(render_template("hello.txt", request=request))


hellobyparam_get = parser.copy()

hellobyparam_get.add_argument(
	"name",
	type=str,
	required=True,
	help="The name to say hello to."
)

@api.response(200, "OK")
@api.response(400, "Input validation failed")
@simple_namespace.route("/hellobyparam")
class HelloByParam(Resource):
	@api.doc(parser=hellobyparam_get)
	def get(self):
		"""
		Says hello

		Says hello to the name specified by arg.
		"""

		request = hellobyparam_get.parse_args(strict=True)

		return(render_template("hello.txt", request=request))


# Post/Put/Delete Exmaples
messages_namespace = api.namespace(
	"Examples - Pt. 2",
	description="Post/Put/Delete examples.",
	path="/"
)

class messages(object):
	def __init__(self):
		"""
		Simple class for holding messages.
		"""

		self.count = 0
		self.messages = []

	def get(self, id=None):
		"""
		Gets a message or messages.
		"""

		if id:
			for m in self.messages:
				if m["id"] == id:
					return(m)

			api.abort(404, "Message {} doesn't exist.".format(id))
		else:
			return(self.messages)

	def create(self, data):
		"""
		Creates a new message."
		"""

		message = data
		message["id"] = self.count = self.count + 1
		self.messages.append(message)

		return(message)

	def update(self, id, message):
		"""
		Updates an existing message."
		"""

		old_message = self.get(id)
		old_message.update(message)

		return(old_message)

	def delete(self, id):
		"""
		Deletes a message."
		"""

		message = self.get(id)
		self.messages.remove(message)


MessageStore = messages()
MessageStore.create({"name": "Bob", "message": "Hi Bob!"})
MessageStore.create({"name": "Carol", "message": "Hi Carol!"})

message = api.model(
	"Message",
	{
		"id": fields.Integer(
			description="The unique message identifier",
			required=True
		),
		"name": fields.String(
			description="The message recipient",
			required=True
		),
		"message": fields.String(
			description="The message content.",
			required=True
		)
	}
)

@messages_namespace.route("/messages")
class MessageList(Resource):
	"""
	Shows a list of messages"
	"""

	@messages_namespace.doc('list_messages')
	@messages_namespace.marshal_list_with(message)
	def get(self):
		"""
		Lists all messages.
		"""

		return MessageStore.messages

	@messages_namespace.doc("create_message")
	@messages_namespace.expect(message)
	@messages_namespace.marshal_with(message, code=201)
	def post(self):
		"""
		Creates a new message.
		"""

		return MessageStore.create(api.payload), 201

@messages_namespace.route("/messages/<int:id>")
@messages_namespace.response(404, "Message not found.")
@messages_namespace.param("id", "The message identifier.")
class Message(Resource):
	"""
	Shows a single message by ID.
	"""

	@messages_namespace.doc("get_message")
	@messages_namespace.marshal_with(message)
	def get(self, id):
		"""
		Show a single message.
		"""

		return MessageStore.get(id)

	@messages_namespace.doc("delete_message")
	@messages_namespace.response(204, "Message deleted")
	@api.header('Authorization', description="Enter 'Bearer &lttoken&gt'", required=True)
	@jwt_required
	def delete(self, id):
		"""
		Delete a message.
		"""

		MessageStore.delete(id)

		return '', 204

	@messages_namespace.expect(message)
	@messages_namespace.marshal_with(message)
	def put(self, id):
		"""
		Update a message.
		"""

		return MessageStore.update(id, api.payload)


# JWT Examples
token_ns = api.namespace(
	"Examples - Pt. 3",
	description="Token authentication.",
	path="/"
)

user_auth = api.model(
	'Auth',
	{
		"username": fields.String(
			description="The name of the user.",
			required=True
		),
		"password": fields.String(
			description="The password of the user.",
			required=True
		),
	}
)

user_auth_parser = parser.copy()

user_auth_parser.add_argument(
	"username",
	type=str,
	required=True,
)

user_auth_parser.add_argument(
	"password",
	type=str,
	required=True,
)

class MessageAuth(object):
	def __init__(self):
		"""
		Manage Authentication (poorly).
		"""

		self.userlist = {}

		self.userlist["test_user"] = "foobar"

	def authenticate(self, username, password):
		"""
		Authenticate a user (poorly).
		"""

		if username not in self.userlist:
			api.abort(403, 'Access denied')

		if self.userlist[username] == password:
			return jsonify({"access_token": create_access_token(identity=username)})

		api.abort(403, 'Access denied')


Authenticator = MessageAuth()

@token_ns.route("/token")
@token_ns.response(403, "Access denied.")
class Authenticate(Resource):
	"""
	Authenticate a user and return a token.
	"""

	@token_ns.doc(parser=user_auth_parser)
	# @token_ns.marshal_with(user_auth)
	def get(self):
		"""
		Authenticate a user by credentials.
		"""

		request = user_auth_parser.parse_args(strict=True)

		result = Authenticator.authenticate(
			request["username"],
			request["password"]
		)

		return result
