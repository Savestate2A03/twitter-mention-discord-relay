from phobbot_dev.commandhandler import ch

class Command(ch.Command): 
    def __init__(self, commandhandler):
        commandlist = [
                {
                    "name": "test",
                    "alias": ["testing", "moretesting"],
                    "function": self.test
                },
                {
                    "name": "testadd",
                    "alias": [],
                    "function": self.test_add_data
                },
                {
                    "name": "testclear",
                    "alias": [],
                    "function": self.test_clear
                },
        ]
        self.commandhandler = commandhandler
        super().__init__(commandlist)

    # testing commands
    def test(self, server, params, message):
        return "server id: " + str(server) + ", server database: " + str(self.commandhandler._server_db(server))

    def test_add_data(self, server, params, message):
        db = self.commandhandler._server_db(server)
        if "test_array" not in db:
            db["test_array"] = []
        db["test_array"].append(params)
        self.commandhandler._save_server_db(server, db)
        return "added '" + params + "' to test database!"

    def test_clear(self, server, params, message):
        db = self.commandhandler._server_db(server)
        db["test_array"] = []
        self.commandhandler._save_server_db(server, db)
        return "cleared test database!"
