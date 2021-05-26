from typing import Tuple, Callable


class ResourcesLocator:
    """
    Class that represents the currently supported resources locator
    """

    resources: dict

    def __init__(self):
        self.resources = {}

        # Courses app locator
        from courses.locator import resources

        self._update_resources(resources)

    def get_resources(self) -> Tuple[str]:
        """
        Returns all currently supported resources
        """
        return tuple(self.resources.keys())

    def get_resolver(self, resource: str) -> Callable:
        """
        Returns a resource resolver from a given resource
        """
        assert resource in self.resources, f"No resource found with the name `{resource}`"
        assert "resolver" in (r := self.resources[resource]), f"No resolver found for `{resource}`"
        return r["resolver"]

    def get_model(self, resource: str) -> Callable:
        """
        Returns a resource model from a given resource
        """
        assert resource in self.resources, f"No resource found with the name `{resource}`"
        assert "model" in (r := self.resources[resource]), f"No model found for `{resource}`"
        return r["model"]

    def _update_resources(self, resources: dict) -> None:
        assert all(
            key in resources for key in self.resources.keys()
        ), "Please make sure that all resources have unique keys"
        self.resources.update(resources)
