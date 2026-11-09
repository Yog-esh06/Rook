from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class WorkloadState:
    namespace: str
    deployment_name: str
    image: str
    desired_replicas: int
    available_replicas: int
    ready: bool
    restart_count: int
    events: list[dict]


class ClusterAdapter(Protocol):
    async def inspect_workload(self, namespace: str, deployment_name: str) -> WorkloadState: ...

    async def apply_release(
        self, namespace: str, deployment_name: str, image: str
    ) -> WorkloadState: ...

    async def rollback(self, namespace: str, deployment_name: str, image: str) -> WorkloadState: ...


class LocalClusterAdapter:
    """Explicit local adapter used when a Kubernetes API is not available."""

    async def inspect_workload(self, namespace: str, deployment_name: str) -> WorkloadState:
        return WorkloadState(namespace, deployment_name, "rook/sample-app:v1", 2, 2, True, 0, [])

    async def apply_release(
        self, namespace: str, deployment_name: str, image: str
    ) -> WorkloadState:
        return WorkloadState(namespace, deployment_name, image, 2, 2, True, 0, [])

    async def rollback(self, namespace: str, deployment_name: str, image: str) -> WorkloadState:
        return WorkloadState(namespace, deployment_name, image, 2, 2, True, 0, [])


class KubernetesClusterAdapter:
    """Optional Kubernetes adapter with lazy client import and bounded operations."""

    def __init__(self, context: str | None = None):
        try:
            from kubernetes import client, config
        except ImportError as exc:
            raise RuntimeError("Install the kubernetes extra to use Kubernetes mode") from exc
        config.load_kube_config(context=context)
        self.apps = client.AppsV1Api()
        self.core = client.CoreV1Api()

    async def inspect_workload(self, namespace: str, deployment_name: str) -> WorkloadState:
        deployment = self.apps.read_namespaced_deployment(deployment_name, namespace)
        status = deployment.status
        return WorkloadState(
            namespace=namespace,
            deployment_name=deployment_name,
            image=deployment.spec.template.spec.containers[0].image,
            desired_replicas=deployment.spec.replicas or 0,
            available_replicas=status.available_replicas or 0,
            ready=(status.ready_replicas or 0) >= (deployment.spec.replicas or 0),
            restart_count=0,
            events=[],
        )

    async def apply_release(
        self, namespace: str, deployment_name: str, image: str
    ) -> WorkloadState:
        deployment = self.apps.read_namespaced_deployment(deployment_name, namespace)
        deployment.spec.template.spec.containers[0].image = image
        self.apps.patch_namespaced_deployment(deployment_name, namespace, deployment)
        return await self.inspect_workload(namespace, deployment_name)

    async def rollback(self, namespace: str, deployment_name: str, image: str) -> WorkloadState:
        return await self.apply_release(namespace, deployment_name, image)
