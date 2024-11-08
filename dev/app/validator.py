import json
import os
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, ValidationError
from pydantic import field_validator
import logging

logger = logging.getLogger('validator')

# Define the global variable to store the validation config
VALIDATION_CONFIG = None

# Load the validation config
class ValidationConfig(BaseModel):
    allowed_fields: List[str]
    allowed_conditions: List[str]
    allowed_actions: List[str]
    time_format: str = "HH:MM"
    
# Load the system config    
class SystemConfig(BaseModel):
    system_name: str
    system_id: Optional[str] = None # Allow none
    agency: Optional[str] = None # Allow none
    product: Optional[str] = None # Allow none
    version: str
    ntp_server: str
    syslog_server: str
    emails: List[str]
    
class Action(BaseModel):
    type: str
    message: Optional[str] = None
    target: Optional[str] = None
    state: Optional[str] = None
    
    @field_validator('type')
    def validate_action_type(cls, v):
        allowed_actions = VALIDATION_CONFIG.allowed_actions
        if v not in allowed_actions:
            raise ValueError(f"Invalid action type: {v}. Allowed actions: {allowed_actions}")
        return v
    
class Rule(BaseModel):
    field: str
    condition: str
    value: Union[int, float]
    actions: List[Action]
    
    @field_validator('field')
    def validate_field(cls, v):
        allowed_fields = VALIDATION_CONFIG.allowed_fields
        if v not in allowed_fields:
            raise ValueError(f"Invalid field: {v}. Allowed fields: {allowed_fields}")
        return v
    
    @field_validator('condition')
    def validate_condition(cls, v):
        allowed_conditions = VALIDATION_CONFIG.allowed_conditions
        if v not in allowed_conditions:
            raise ValueError(f"Invalid condition: {v}. Allowed conditions: {allowed_conditions}")
        return v
    
class Schedule(BaseModel):
    enabled: bool
    every_day: bool
    days: List[str]
    on_time: str
    off_time: str
    
    @field_validator('days')
    def validate_days(cls, v, info):
        every_day = info.data.get('every_day')
        if not every_day and not v:
            raise ValueError("Days must be provided if 'every_day' is False")
        allowed_days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        for day in v:
            if day.lower() not in allowed_days:
                raise ValueError(f"Invalid day: {day}. Allowed days: {allowed_days}")
        return v
    
    @field_validator('on_time', 'off_time')
    def validate_time_format(cls, v):
        time_format = VALIDATION_CONFIG.time_format
        from datetime import datetime
        try:
            datetime.strptime(v, time_format)
        except ValueError:
            raise ValueError(f"Invalid time format: {v}. Must be in the format: {time_format}")
        return v
            
class RelayConfig(BaseModel):
    name: str
    pin: int
    address: str
    boot_power: bool = False
    monitor: bool = False
    schedule: Optional[Union[Schedule, bool]] = None
    rules: Optional[Union[Dict[str, Rule], bool]] = None
    
    @field_validator('pin', 'address', mode='before')
    def immutable_fields(cls, v):
        # Prevent changing the pin or address
        return v
    
# Define the full config model
class FullConfig(BaseModel):
    system: SystemConfig
    relays: Dict[str, RelayConfig]
    validation: ValidationConfig
    
def load_json_file(filepath: str) -> dict:
    with open(filepath, 'r') as file:
        return json.load(file)

def merge_configs(default: Dict[str, Any], custom: Dict[str, Any]) -> Dict[str, Any]:
    merged = default.copy()
    for key, value in custom.items():
        if key in default:
            if isinstance(value, dict) and isinstance(default[key], dict):
                merged[key] = merge_configs(default[key], value)
            else:
                # Enforce immutability for the relay pin and address
                if key == "relays":
                    for relay_id, relay_config in value.items():
                        if relay_id in default["relays"]:
                            relay_default = default["relays"][relay_id]
                            relay_merged = relay_default.copy()
                            for r_key, r_value in relay_config.items():
                                if r_key not in ["pin", "address"]:
                                    relay_merged[r_key] = r_value
                            merged["relays"][relay_id] = relay_merged
                        else:
                            merged["relays"][relay_id] = relay_config
                else:
                    merged[key] = value
        else:
            merged[key] = value
    return merged

def remove_invalid_value(config_data: dict, loc: tuple):
    d = config_data
    for key in loc[:-1]:
        d = d.get(key, {})
    # Remove the invalid key
    d.pop(loc[-1], None)
    
def handle_validation_errors(config_data: dict, validation_error: ValidationError) -> FullConfig:
    # Extract error locations
    for error in validation_error.errors():
        loc = error['loc']
        logger.warning(f"Invalid value at {'.'.join(map(str, loc))}: {error['msg']}")
        remove_invalid_value(config_data, loc)
    try:
        config = FullConfig(**config_data)
        logger.info("Configuration re-validated successfully after correction")
    except ValidationError as e:
        logger.error(f"Failed to re-validate configuration after correction: {e}")
        raise e # Raise the error if re-validation fails, Need to make sure this is not terminating the program
    return config

def validate_config() -> FullConfig:
    global VALIDATION_CONFIG
    # Load the default config
    default_config_data = load_json_file('dev/default_config.json')
    
    # Get the Raspberry Pi Serial Number
    default_system_id = pi_serial()
    default_config_data['system']['system_id'] = default_system_id
    
    # Set VALIDATION_CONFIG from the default config
    VALIDATION_CONFIG = ValidationConfig(**default_config_data.get('validation', {}))
    
    # Load the custom config if it exists
    if os.path.exists('custom_config.json'):
        custom_config_data = load_json_file('custom_config.json')
    else:
        custom_config_data = {}
    
    # Merge the default and custom configs
    merged_config_data = merge_configs(default_config_data, custom_config_data)
    
    # After merging configs, check system_id
    system_id = merged_config_data['system'].get('system_id')
    if system_id is None:
        system_id = pi_serial()
        merged_config_data['system']['system_id'] = system_id
    
    
    # Validate the merged config
    try:
        config = FullConfig(**merged_config_data)
        logger.info("Configuration validated successfully")
    except ValidationError as e:
        logger.error(f"Failed to validate configuration: {e}")
        config = handle_validation_errors(merged_config_data, e)        
    return config


# Function to get the Raspberry Pi Serial Number, used as the default system_id if not provided
def pi_serial():
    try:
        with open('/proc/cpuinfo', 'r') as f:
            for line in f:
                if line.startswith('Serial'):
                    serial = line.strip().split(':')[1].strip()
                    return serial
    except Exception as e:
        print(f"Unable to read serial number: {e}")
    return "UNKNOWN_SERIAL"

system_id = pi_serial()