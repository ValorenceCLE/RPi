import asyncio
from typing import Dict, List
from utils.validator import Action, Rule
from utils.logging_setup import local_logger as logger
from utils.logging_setup import central_logger as syslog

class RulesEngine:
    def __init__(self, relay_id: str, rules: Dict[str, Rule]):
        self.relay_id = relay_id
        self.rules = rules
    
    async def evaluate_rules(self, data: Dict[str, float]):
        if not self.rules or self.rules is False:
            return
        for rule_id, rule in self.rules.items():
            field_value = data.get(rule.field)
            if field_value is None:
                logger.error(f"Field {rule.field} not found in data")
                continue
            if self.evaluate_condition(field_value, rule.condition, rule.value):
                await self.execute_actions(rule.actions)
    
    def evaluate_condition(self, field_value, condition, value) -> bool:
        if condition == ">":
            return field_value > value
        elif condition == "<":
            return field_value < value
        elif condition == ">=":
            return field_value >= value
        elif condition == "<=":
            return field_value <= value
        elif condition == "==":
            return field_value == value
        elif condition == "!=":
            return field_value != value
        else:
            logger.error(f"Invalid condition: {condition}")
            return False

    async def execute_actions(self, actions: List[Action]):
        for action in actions:
            if action.type == "log":
                message = action.message or f"Rule triggered in {self.relay_id}."
                syslog.info(message)
            elif action.type == "email":
                message = action.message or f"Rule triggered in {self.relay_id}."
                # Implement email sending logic here
                logger.info(f"Sending email: {message}")
            elif action.type == "toggle_relay":
                target_relay_id = action.target
                state = action.state
                # Implement relay toggling logic here
                logger.info(f"Toggling {target_relay_id} to state {state}.")
            elif action.type == "mqtt":
                message = action.message or f"Rule triggered in {self.relay_id}."
                # Implement MQTT publishing logic here
                logger.info(f"Publishing MQTT message: {message}")
            elif action.type == "restart":
                # Implement restart logic here
                logger.info(f"Restarting system as per rule in {self.relay_id}.")
            elif action.type == "shutdown":
                # Implement shutdown logic here
                logger.info(f"Shutting down system as per rule in {self.relay_id}.")
            else:
                logger.error(f"Unknown action type: {action.type}")