from __future__ import unicode_literals

import ipaddress

from sqlalchemy import TypeDecorator
from sqlalchemy.dialects.postgresql import CIDR


class _AlwaysSortableMixin(object):
    def __lt__(self, other):
        if self._version != other._version:
            return self._version < other._version
        else:
            return super(_AlwaysSortableMixin, self).__lt__(other)


class IPv4Network(_AlwaysSortableMixin, ipaddress.IPv4Network):
    pass


class IPv6Network(_AlwaysSortableMixin, ipaddress.IPv6Network):
    pass


def _ip_network(address, strict=True):
    # based on `ipaddress.ip_network` but returns always-sortable classes
    # since sqlalchemy needs to be able to sort all values of a type
    address = unicode(address)
    try:
        return IPv4Network(address, strict)
    except (ipaddress.AddressValueError, ipaddress.NetmaskValueError):
        pass

    try:
        return IPv6Network(address, strict)
    except (ipaddress.AddressValueError, ipaddress.NetmaskValueError):
        pass

    raise ValueError('%r does not appear to be an IPv4 or IPv6 network' % address)


class PyIPNetwork(TypeDecorator):
    """Custom type which handles values from a PEP-3144 ip network."""

    impl = CIDR

    def process_bind_param(self, value, dialect):
        return unicode(_ip_network(value)) if value is not None else None

    def process_result_value(self, value, dialect):
        return _ip_network(value) if value is not None else None

    def coerce_set_value(self, value):
        return _ip_network(value) if value is not None else None

    def alembic_render_type(self, autogen_context):
        autogen_context.imports.add('from snms.core.db.sqlalchemy import PyIPNetwork')
        return '{}()'.format(type(self).__name__)
