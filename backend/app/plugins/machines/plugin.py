# backend/app/plugins/machines/plugin.py
class MachineManagementPlugin(Plugin):
    @classmethod
    def get_metadata(cls) -> PluginMetadata:
        return PluginMetadata(
            name="machine_management",
            version="1.0.0",
            description="Manages remote machines and their connections",
            dependencies=["ssh", "paramiko"],
            requires_auth=True
        )

    @classmethod
    def initialize(cls) -> 'MachineManagementPlugin':
        plugin = cls()
        plugin.setup_routes()
        return plugin

    def setup_routes(self):
        @self.router.post("/machines")
        async def add_machine(machine: Machine):
            # Implementation...
            pass

        @self.router.get("/machines")
        async def list_machines():
            # Implementation...
            pass
