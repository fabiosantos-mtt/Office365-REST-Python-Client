from office365.runtime.client_object import ClientObject
from office365.runtime.client_query import UpdateEntityQuery
from office365.runtime.odata.odata_path_parser import ODataPathParser
from office365.runtime.resource_path_entity import ResourcePathEntity


class Principal(ClientObject):
    """Represents a user or group that can be assigned permissions to control security."""

    @property
    def id(self):
        """Gets a value that specifies the member identifier for the user or group."""
        if self.is_property_available('Id'):
            return self.properties['Id']
        else:
            return None

    @property
    def title(self):
        """Gets a value that specifies the name of the principal."""
        if self.is_property_available('Title'):
            return self.properties['Title']
        else:
            return None

    @title.setter
    def title(self, value):
        self.properties['Title'] = value

    @property
    def login_name(self):
        """Gets the login name of the principal."""
        if self.is_property_available('LoginName'):
            return self.properties['LoginName']
        else:
            return None

    @property
    def is_hidden_in_ui(self):
        """Gets the login name of the principal."""
        if self.is_property_available('IsHiddenInUI'):
            return self.properties['IsHiddenInUI']
        else:
            return None

    @property
    def principal_type(self):
        """Gets the login name of the principal."""
        if self.is_property_available('PrincipalType'):
            return self.properties['PrincipalType']
        else:
            return None

    def set_property(self, name, value, serializable=True):
        super(Principal, self).set_property(name, value, serializable)
        # fallback: create a new resource path
        if self._resource_path is None:
            if name == "Id":
                self._resource_path = ResourcePathEntity(
                    self.context,
                    self._parent_collection.resourcePath,
                    ODataPathParser.from_method("GetById", [value]))
            elif name == "LoginName":
                self._resource_path = ResourcePathEntity(
                    self.context,
                    self._parent_collection.resourcePath,
                    ODataPathParser.from_method("GetByName", [value]))

    def update(self):
        """Update a User or Group resource"""
        qry = UpdateEntityQuery(self)
        self.context.add_query(qry)
