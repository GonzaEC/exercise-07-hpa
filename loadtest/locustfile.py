import random
import string

from locust import HttpUser, between, task


def _rand_name(length: int = 8) -> str:
    """Generate a random alphanumeric string."""
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))


class NodeRegistryUser(HttpUser):
    """Simulates a client that exercises the Node Registry API."""

    # Wait 0.5 – 2 seconds between consecutive tasks
    wait_time = between(0.5, 2)

    @task(3)
    def check_health(self):
        """Hit the health endpoint — lightweight, high frequency."""
        self.client.get("/health", name="/health")

    @task(2)
    def list_nodes(self):
        """Retrieve the full node list."""
        self.client.get("/api/nodes", name="/api/nodes")

    @task(1)
    def register_and_query_node(self):
        """Register a unique node then immediately query it by name."""
        name = f"node-{_rand_name()}"
        payload = {
            "name": name,
            "host": f"10.0.{random.randint(0, 255)}.{random.randint(1, 254)}",
            "port": random.randint(1024, 65535),
        }
        with self.client.post(
            "/api/nodes",
            json=payload,
            name="/api/nodes [POST]",
            catch_response=True,
        ) as resp:
            if resp.status_code == 201:
                resp.success()
                # Follow up with a GET for the same node
                self.client.get(
                    f"/api/nodes/{name}",
                    name="/api/nodes/{name}",
                )
            elif resp.status_code == 409:
                # Name collision — treat as success (node already exists)
                resp.success()
            else:
                resp.failure(f"Unexpected status {resp.status_code}")
