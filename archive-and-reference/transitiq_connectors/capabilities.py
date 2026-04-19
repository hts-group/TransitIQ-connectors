"""Connector capability model.

The model here describes technical connector abilities, not canonical product
meaning. Normalization into canonical TransitIQ semantics is handled outside
this repository by control-plane owned contracts.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import FrozenSet, Tuple


class Capability(str, Enum):
    CONNECT = "connect"
    DISCOVERY = "discovery"
    OBSERVED_STATUS = "observed_status"
    MESSAGE_POST = "message_post"
    BRIGHTNESS_CONTROL = "brightness_control"
    PLAYLIST_CONTROL = "playlist_control"
    CONTROL_MODE = "control_mode"
    TEMPLATE_ACTIVATION = "template_activation"
    PREDEFINED_MESSAGE_ACTIVATION = "predefined_message_activation"


class AuthMode(str, Enum):
    SNMP_V1 = "snmp_v1"
    SNMP_V2C = "snmp_v2c"
    SNMP_V3 = "snmp_v3"
    NETWORK_PATH_TRUST = "network_path_trust"
    MQTT_CREDENTIALS = "mqtt_credentials"
    HTTP_BASIC = "http_basic"
    NO_AUTH = "none"


@dataclass(frozen=True)
class AuthProfile:
    """Connector-local authentication declaration.

    This declares transport/auth mechanics only. Secret storage, policy, and
    canonical auth semantics are owned by control-plane and platform services.
    """

    supported_modes: Tuple[AuthMode, ...]
    required_secret_fields: Tuple[str, ...]
    notes: Tuple[str, ...] = ()


@dataclass(frozen=True)
class CapabilityProfile:
    """Describes what an adapter can do, plus transport/auth hints."""

    supported: FrozenSet[Capability]
    transport: Tuple[str, ...]
    auth: AuthProfile
    notes: Tuple[str, ...] = ()


NTCIP_CAPABILITIES = CapabilityProfile(
    supported=frozenset(
        {
            Capability.CONNECT,
            Capability.DISCOVERY,
            Capability.OBSERVED_STATUS,
            Capability.MESSAGE_POST,
            Capability.BRIGHTNESS_CONTROL,
            Capability.CONTROL_MODE,
        }
    ),
    transport=("snmp",),
    auth=AuthProfile(
        supported_modes=(AuthMode.SNMP_V1, AuthMode.SNMP_V2C, AuthMode.SNMP_V3),
        required_secret_fields=("community_or_user", "auth_or_priv_keys_optional"),
    ),
    notes=(
        "Message payloads are device protocol specific.",
        "Control mode operations target sign-local runtime state.",
    ),
)

YAHAM_CAPABILITIES = CapabilityProfile(
    supported=frozenset(
        {
            Capability.CONNECT,
            Capability.DISCOVERY,
            Capability.OBSERVED_STATUS,
            Capability.BRIGHTNESS_CONTROL,
            Capability.PLAYLIST_CONTROL,
        }
    ),
    transport=("tcp", "udp", "mqtt"),
    auth=AuthProfile(
        supported_modes=(AuthMode.NETWORK_PATH_TRUST, AuthMode.MQTT_CREDENTIALS),
        required_secret_fields=("mqtt_username_optional", "mqtt_password_optional"),
    ),
    notes=(
        "MQTT support is adapter-local and keeps vendor topic detail encapsulated.",
    ),
)

SOLARI_CAPABILITIES = CapabilityProfile(
    supported=frozenset(
        {
            Capability.CONNECT,
            Capability.DISCOVERY,
            Capability.OBSERVED_STATUS,
            Capability.CONTROL_MODE,
            Capability.PREDEFINED_MESSAGE_ACTIVATION,
            Capability.TEMPLATE_ACTIVATION,
        }
    ),
    transport=("soap_http", "soap_https"),
    auth=AuthProfile(
        supported_modes=(AuthMode.NO_AUTH, AuthMode.HTTP_BASIC),
        required_secret_fields=("username_optional", "password_optional"),
    ),
    notes=(
        "SOAP payload schemas remain vendor/FEP specific within the adapter boundary.",
    ),
)

REMOTE_COUNTER_DEMO_CAPABILITIES = CapabilityProfile(
    supported=frozenset(
        {
            Capability.CONNECT,
            Capability.DISCOVERY,
            Capability.OBSERVED_STATUS,
        }
    ),
    transport=("mqtt",),
    auth=AuthProfile(
        supported_modes=(AuthMode.MQTT_CREDENTIALS, AuthMode.NETWORK_PATH_TRUST),
        required_secret_fields=("mqtt_username_optional", "mqtt_password_optional"),
    ),
    notes=(
        "Demo slice is monitoring-first and does not expose control operations.",
        "Ingestion path follows remote-counter rp2350 firmware MQTT publication flow.",
    ),
)
