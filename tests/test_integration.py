#!/usr/bin/env python3
"""
ScreenPilot Home Assistant Integration Validator

This test script validates the structure and correctness of the ScreenPilot
Home Assistant integration without requiring Home Assistant or pytest-homeassistant.

Run with: python3 tests/test_integration.py

Dependencies: None (uses only Python standard library)
Optional: PyYAML for better YAML parsing (pip install pyyaml)
"""

from __future__ import annotations

import ast
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

# Add the custom_components directory to the path
REPO_ROOT = Path(__file__).parent.parent
COMPONENTS_PATH = REPO_ROOT / "custom_components" / "screenpilot"
sys.path.insert(0, str(REPO_ROOT))


# Simple YAML parser for services.yaml validation (no external dependencies)
def simple_yaml_parse(content: str) -> dict[str, Any]:
    """
    Parse a simple YAML file structure (enough for services.yaml validation).
    This is NOT a full YAML parser - just handles the specific structure we need.
    """
    result: dict[str, Any] = {}
    current_service: str | None = None
    current_section: str | None = None
    current_field: str | None = None

    lines = content.split('\n')

    for line in lines:
        # Skip empty lines and comments
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue

        # Calculate indentation level
        indent = len(line) - len(line.lstrip())

        # Top-level service (no indentation)
        if indent == 0 and ':' in line:
            current_service = stripped.rstrip(':')
            result[current_service] = {}
            current_section = None
            current_field = None
        # Second level (service properties like name, description, fields)
        elif indent == 2 and current_service and ':' in stripped:
            parts = stripped.split(':', 1)
            key = parts[0].strip()
            value = parts[1].strip() if len(parts) > 1 else ""

            if key == 'fields':
                result[current_service]['fields'] = {}
                current_section = 'fields'
                current_field = None
            else:
                result[current_service][key] = value.strip('"\'') if value else ""
                current_section = key
        # Third level (field names under fields)
        elif indent == 4 and current_service and current_section == 'fields' and ':' in stripped:
            field_name = stripped.rstrip(':')
            result[current_service]['fields'][field_name] = {}
            current_field = field_name
        # Fourth level and beyond (field properties) - we don't need to parse these

    return result


# Try to import PyYAML for better parsing, fall back to simple parser
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


class TestResult:
    """Simple test result tracker."""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors: list[str] = []

    def ok(self, name: str) -> None:
        """Record a passed test."""
        print(f"  [PASS] {name}")
        self.passed += 1

    def fail(self, name: str, reason: str) -> None:
        """Record a failed test."""
        print(f"  [FAIL] {name}: {reason}")
        self.failed += 1
        self.errors.append(f"{name}: {reason}")

    def summary(self) -> bool:
        """Print summary and return True if all passed."""
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"Results: {self.passed}/{total} tests passed")
        if self.errors:
            print("\nFailures:")
            for error in self.errors:
                print(f"  - {error}")
        print("=" * 60)
        return self.failed == 0


def load_module_ast(filepath: Path) -> ast.Module:
    """Load a Python file as an AST without executing it."""
    with open(filepath, "r") as f:
        return ast.parse(f.read(), filename=str(filepath))


def get_class_names(module: ast.Module) -> list[str]:
    """Extract class names from an AST module."""
    return [node.name for node in ast.walk(module) if isinstance(node, ast.ClassDef)]


def get_function_names(module: ast.Module) -> list[str]:
    """Extract top-level function names from an AST module."""
    return [
        node.name
        for node in module.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]


def get_dataclass_fields(module: ast.Module, class_name: str) -> list[str]:
    """Extract field names from a dataclass definition."""
    fields = []
    for node in ast.walk(module):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for item in node.body:
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    fields.append(item.target.id)
    return fields


class TestModuleImports:
    """Test that all modules can be parsed correctly."""

    def __init__(self, result: TestResult):
        self.result = result

    def run(self) -> None:
        """Run all import tests."""
        print("\n1. Testing Module Structure (AST parsing)")
        print("-" * 40)

        modules = [
            "__init__.py",
            "api.py",
            "config_flow.py",
            "const.py",
            "coordinator.py",
            "entity.py",
            "binary_sensor.py",
            "button.py",
            "camera.py",
            "number.py",
            "select.py",
            "sensor.py",
            "switch.py",
            "text.py",
        ]

        for module_name in modules:
            filepath = COMPONENTS_PATH / module_name
            if not filepath.exists():
                self.result.fail(f"Module {module_name}", "File not found")
                continue

            try:
                load_module_ast(filepath)
                self.result.ok(f"Module {module_name} parses correctly")
            except SyntaxError as e:
                self.result.fail(f"Module {module_name}", f"Syntax error: {e}")


class TestEntityDescriptions:
    """Test that all entity descriptions are valid."""

    def __init__(self, result: TestResult):
        self.result = result

    def run(self) -> None:
        """Run all entity description tests."""
        print("\n2. Testing Entity Descriptions")
        print("-" * 40)

        self._test_sensor_descriptions()
        self._test_binary_sensor_descriptions()
        self._test_button_descriptions()
        self._test_switch_descriptions()

    def _test_sensor_descriptions(self) -> None:
        """Test sensor entity descriptions."""
        module = load_module_ast(COMPONENTS_PATH / "sensor.py")

        # Check for SENSORS tuple (can be Assign or AnnAssign with type annotation)
        sensors_found = False
        for node in ast.walk(module):
            # Check regular assignment
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "SENSORS":
                        sensors_found = True
                        if isinstance(node.value, ast.Tuple):
                            count = len(node.value.elts)
                            self.result.ok(f"Sensor descriptions: {count} sensors defined")
                        else:
                            self.result.fail("Sensor descriptions", "SENSORS should be a tuple")
            # Check annotated assignment (e.g., SENSORS: tuple[...] = (...))
            elif isinstance(node, ast.AnnAssign):
                if isinstance(node.target, ast.Name) and node.target.id == "SENSORS":
                    sensors_found = True
                    if node.value and isinstance(node.value, ast.Tuple):
                        count = len(node.value.elts)
                        self.result.ok(f"Sensor descriptions: {count} sensors defined")
                    else:
                        self.result.fail("Sensor descriptions", "SENSORS should be a tuple")

        if not sensors_found:
            self.result.fail("Sensor descriptions", "SENSORS tuple not found")

        # Check ScreenPilotSensorDescription class exists
        classes = get_class_names(module)
        if "ScreenPilotSensorDescription" in classes:
            self.result.ok("ScreenPilotSensorDescription class defined")
        else:
            self.result.fail("Sensor descriptions", "ScreenPilotSensorDescription not found")

    def _test_binary_sensor_descriptions(self) -> None:
        """Test binary sensor entity descriptions."""
        module = load_module_ast(COMPONENTS_PATH / "binary_sensor.py")

        # Check for BINARY_SENSORS tuple (can be Assign or AnnAssign)
        sensors_found = False
        for node in ast.walk(module):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "BINARY_SENSORS":
                        sensors_found = True
                        if isinstance(node.value, ast.Tuple):
                            count = len(node.value.elts)
                            self.result.ok(f"Binary sensor descriptions: {count} sensors defined")
            elif isinstance(node, ast.AnnAssign):
                if isinstance(node.target, ast.Name) and node.target.id == "BINARY_SENSORS":
                    sensors_found = True
                    if node.value and isinstance(node.value, ast.Tuple):
                        count = len(node.value.elts)
                        self.result.ok(f"Binary sensor descriptions: {count} sensors defined")

        if not sensors_found:
            self.result.fail("Binary sensor descriptions", "BINARY_SENSORS tuple not found")

        classes = get_class_names(module)
        if "ScreenPilotBinarySensorDescription" in classes:
            self.result.ok("ScreenPilotBinarySensorDescription class defined")
        else:
            self.result.fail("Binary sensor descriptions", "ScreenPilotBinarySensorDescription not found")

    def _test_button_descriptions(self) -> None:
        """Test button entity descriptions."""
        module = load_module_ast(COMPONENTS_PATH / "button.py")

        buttons_found = False
        for node in ast.walk(module):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "BUTTONS":
                        buttons_found = True
                        if isinstance(node.value, ast.Tuple):
                            count = len(node.value.elts)
                            self.result.ok(f"Button descriptions: {count} buttons defined")
            elif isinstance(node, ast.AnnAssign):
                if isinstance(node.target, ast.Name) and node.target.id == "BUTTONS":
                    buttons_found = True
                    if node.value and isinstance(node.value, ast.Tuple):
                        count = len(node.value.elts)
                        self.result.ok(f"Button descriptions: {count} buttons defined")

        if not buttons_found:
            self.result.fail("Button descriptions", "BUTTONS tuple not found")

        classes = get_class_names(module)
        if "ScreenPilotButtonDescription" in classes:
            self.result.ok("ScreenPilotButtonDescription class defined")
        else:
            self.result.fail("Button descriptions", "ScreenPilotButtonDescription not found")

    def _test_switch_descriptions(self) -> None:
        """Test switch entity descriptions."""
        module = load_module_ast(COMPONENTS_PATH / "switch.py")

        switches_found = False
        for node in ast.walk(module):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "SWITCHES":
                        switches_found = True
                        if isinstance(node.value, ast.Tuple):
                            count = len(node.value.elts)
                            self.result.ok(f"Switch descriptions: {count} switches defined")
            elif isinstance(node, ast.AnnAssign):
                if isinstance(node.target, ast.Name) and node.target.id == "SWITCHES":
                    switches_found = True
                    if node.value and isinstance(node.value, ast.Tuple):
                        count = len(node.value.elts)
                        self.result.ok(f"Switch descriptions: {count} switches defined")

        if not switches_found:
            self.result.fail("Switch descriptions", "SWITCHES tuple not found")

        classes = get_class_names(module)
        if "ScreenPilotSwitchDescription" in classes:
            self.result.ok("ScreenPilotSwitchDescription class defined")
        else:
            self.result.fail("Switch descriptions", "ScreenPilotSwitchDescription not found")


class TestCoordinatorDataClass:
    """Test that the coordinator data class is properly structured."""

    def __init__(self, result: TestResult):
        self.result = result

    def run(self) -> None:
        """Run coordinator data tests."""
        print("\n3. Testing Coordinator Data Class")
        print("-" * 40)

        module = load_module_ast(COMPONENTS_PATH / "coordinator.py")

        # Check ScreenPilotData class exists
        classes = get_class_names(module)
        if "ScreenPilotData" not in classes:
            self.result.fail("Coordinator", "ScreenPilotData class not found")
            return

        self.result.ok("ScreenPilotData class defined")

        # Get the dataclass fields
        fields = get_dataclass_fields(module, "ScreenPilotData")

        # Expected fields based on the data class
        required_fields = [
            "hostname",
            "ip_address",
            "uptime",
            "cpu_percent",
            "memory_percent",
            "disk_percent",
            "system_healthy",
            "health_status",
            "browser_connected",
            "browser_healthy",
            "current_url",
            "startup_url",
            "zoom_level",
            "session_mode",
            "tv_present",
            "tv_power_on",
        ]

        missing_fields = [f for f in required_fields if f not in fields]
        if missing_fields:
            self.result.fail("ScreenPilotData fields", f"Missing: {missing_fields}")
        else:
            self.result.ok(f"ScreenPilotData has {len(fields)} fields defined")

        # Check for dataclass decorator
        dataclass_found = False
        for node in module.body:
            if isinstance(node, ast.ClassDef) and node.name == "ScreenPilotData":
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Name) and decorator.id == "dataclass":
                        dataclass_found = True
                    elif isinstance(decorator, ast.Call):
                        if isinstance(decorator.func, ast.Name) and decorator.func.id == "dataclass":
                            dataclass_found = True

        if dataclass_found:
            self.result.ok("ScreenPilotData uses @dataclass decorator")
        else:
            self.result.fail("ScreenPilotData", "@dataclass decorator not found")

        # Check ScreenPilotCoordinator class
        if "ScreenPilotCoordinator" in classes:
            self.result.ok("ScreenPilotCoordinator class defined")
        else:
            self.result.fail("Coordinator", "ScreenPilotCoordinator class not found")

        # Check for _async_update_data method
        update_method_found = False
        for node in ast.walk(module):
            if isinstance(node, ast.ClassDef) and node.name == "ScreenPilotCoordinator":
                for item in node.body:
                    if isinstance(item, ast.AsyncFunctionDef) and item.name == "_async_update_data":
                        update_method_found = True

        if update_method_found:
            self.result.ok("ScreenPilotCoordinator._async_update_data method defined")
        else:
            self.result.fail("Coordinator", "_async_update_data method not found")


class TestAPIClient:
    """Test that the API client has all required methods."""

    def __init__(self, result: TestResult):
        self.result = result

    def run(self) -> None:
        """Run API client tests."""
        print("\n4. Testing API Client")
        print("-" * 40)

        module = load_module_ast(COMPONENTS_PATH / "api.py")

        # Check ScreenPilotAPI class exists
        classes = get_class_names(module)
        if "ScreenPilotAPI" not in classes:
            self.result.fail("API Client", "ScreenPilotAPI class not found")
            return

        self.result.ok("ScreenPilotAPI class defined")

        # Check for required exception classes
        expected_exceptions = ["ScreenPilotError", "ScreenPilotConnectionError", "ScreenPilotAuthError"]
        for exc in expected_exceptions:
            if exc in classes:
                self.result.ok(f"Exception class {exc} defined")
            else:
                self.result.fail("API exceptions", f"{exc} not found")

        # Extract methods from ScreenPilotAPI class
        api_methods = []
        for node in ast.walk(module):
            if isinstance(node, ast.ClassDef) and node.name == "ScreenPilotAPI":
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        api_methods.append(item.name)

        # Required API methods based on the integration
        required_methods = [
            "__init__",
            "base_url",
            "_headers",
            "_request",
            "_get",
            "_post",
            "_put",
            "test_connection",
            "get_system_info",
            "get_health",
            "get_service_status",
            "reboot_system",
            "get_kiosk_url",
            "set_kiosk_url",
            "get_startup_url",
            "set_startup_url",
            "get_kiosk_health",
            "reload_page",
            "hard_refresh",
            "restart_browser",
            "clear_data",
            "get_zoom",
            "set_zoom",
            "set_session_mode",
            "execute_javascript",
            "get_cec_status",
            "send_cec_command",
            "get_screenshot_url",
            "get_screenshot",
        ]

        missing_methods = [m for m in required_methods if m not in api_methods]
        if missing_methods:
            self.result.fail("API methods", f"Missing: {missing_methods}")
        else:
            self.result.ok(f"All {len(required_methods)} required API methods present")


class TestConfigFlow:
    """Test that config_flow follows the correct pattern."""

    def __init__(self, result: TestResult):
        self.result = result

    def run(self) -> None:
        """Run config flow tests."""
        print("\n5. Testing Config Flow")
        print("-" * 40)

        module = load_module_ast(COMPONENTS_PATH / "config_flow.py")

        # Check ConfigFlow class exists
        classes = get_class_names(module)
        if "ConfigFlow" not in classes:
            self.result.fail("Config Flow", "ConfigFlow class not found")
            return

        self.result.ok("ConfigFlow class defined")

        # Check for domain attribute
        version_found = False
        async_step_user_found = False

        for node in ast.walk(module):
            if isinstance(node, ast.ClassDef) and node.name == "ConfigFlow":
                # Check class body for VERSION and async_step_user
                for item in node.body:
                    if isinstance(item, ast.Assign):
                        for target in item.targets:
                            if isinstance(target, ast.Name) and target.id == "VERSION":
                                version_found = True
                    if isinstance(item, ast.AsyncFunctionDef) and item.name == "async_step_user":
                        async_step_user_found = True

        if version_found:
            self.result.ok("ConfigFlow.VERSION defined")
        else:
            self.result.fail("Config Flow", "VERSION attribute not found")

        if async_step_user_found:
            self.result.ok("ConfigFlow.async_step_user method defined")
        else:
            self.result.fail("Config Flow", "async_step_user method not found")

        # Check for STEP_USER_DATA_SCHEMA
        schema_found = False
        for node in module.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "STEP_USER_DATA_SCHEMA":
                        schema_found = True

        if schema_found:
            self.result.ok("STEP_USER_DATA_SCHEMA defined")
        else:
            self.result.fail("Config Flow", "STEP_USER_DATA_SCHEMA not found")


class TestServicesYAML:
    """Test that services.yaml is valid YAML."""

    def __init__(self, result: TestResult):
        self.result = result

    def run(self) -> None:
        """Run services.yaml tests."""
        print("\n6. Testing services.yaml")
        print("-" * 40)

        services_path = COMPONENTS_PATH / "services.yaml"
        if not services_path.exists():
            self.result.fail("services.yaml", "File not found")
            return

        try:
            with open(services_path, "r") as f:
                content = f.read()

            # Try PyYAML first, fall back to simple parser
            if YAML_AVAILABLE:
                services = yaml.safe_load(content)
                self.result.ok("services.yaml is valid YAML (verified with PyYAML)")
            else:
                services = simple_yaml_parse(content)
                self.result.ok("services.yaml structure is valid (basic check)")

        except Exception as e:
            self.result.fail("services.yaml", f"Parse error: {e}")
            return

        if not isinstance(services, dict):
            self.result.fail("services.yaml", "Should contain a dictionary of services")
            return

        # Expected services based on const.py
        expected_services = [
            "load_url",
            "execute_javascript",
            "send_cec_command",
            "clear_data",
            "set_zoom",
        ]

        for service in expected_services:
            if service in services:
                self.result.ok(f"Service '{service}' defined")

                # Check required fields
                svc = services[service]
                if "name" not in svc:
                    self.result.fail(f"Service {service}", "Missing 'name' field")
                if "description" not in svc:
                    self.result.fail(f"Service {service}", "Missing 'description' field")
                if "fields" not in svc:
                    self.result.fail(f"Service {service}", "Missing 'fields' field")
            else:
                self.result.fail("services.yaml", f"Missing service: {service}")


class TestInitSetup:
    """Test the __init__.py setup functions."""

    def __init__(self, result: TestResult):
        self.result = result

    def run(self) -> None:
        """Run __init__.py tests."""
        print("\n7. Testing __init__.py Setup")
        print("-" * 40)

        module = load_module_ast(COMPONENTS_PATH / "__init__.py")

        # Check required functions
        functions = get_function_names(module)

        if "async_setup_entry" in functions:
            self.result.ok("async_setup_entry function defined")
        else:
            self.result.fail("__init__.py", "async_setup_entry function not found")

        if "async_unload_entry" in functions:
            self.result.ok("async_unload_entry function defined")
        else:
            self.result.fail("__init__.py", "async_unload_entry function not found")

        if "async_setup_services" in functions:
            self.result.ok("async_setup_services function defined")
        else:
            self.result.fail("__init__.py", "async_setup_services function not found")

        # Check PLATFORMS list (can be Assign or AnnAssign)
        platforms_found = False
        for node in module.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "PLATFORMS":
                        platforms_found = True
                        if isinstance(node.value, ast.List):
                            count = len(node.value.elts)
                            self.result.ok(f"PLATFORMS list defined with {count} platforms")
            elif isinstance(node, ast.AnnAssign):
                if isinstance(node.target, ast.Name) and node.target.id == "PLATFORMS":
                    platforms_found = True
                    if node.value and isinstance(node.value, ast.List):
                        count = len(node.value.elts)
                        self.result.ok(f"PLATFORMS list defined with {count} platforms")

        if not platforms_found:
            self.result.fail("__init__.py", "PLATFORMS list not found")


class TestManifest:
    """Test the manifest.json file."""

    def __init__(self, result: TestResult):
        self.result = result

    def run(self) -> None:
        """Run manifest.json tests."""
        print("\n8. Testing manifest.json")
        print("-" * 40)

        manifest_path = COMPONENTS_PATH / "manifest.json"
        if not manifest_path.exists():
            self.result.fail("manifest.json", "File not found")
            return

        try:
            with open(manifest_path, "r") as f:
                manifest = json.load(f)
        except json.JSONDecodeError as e:
            self.result.fail("manifest.json", f"Invalid JSON: {e}")
            return

        self.result.ok("manifest.json is valid JSON")

        # Check required fields
        required_fields = {
            "domain": "screenpilot",
            "name": "ScreenPilot",
            "config_flow": True,
        }

        for field, expected_value in required_fields.items():
            if field not in manifest:
                self.result.fail("manifest.json", f"Missing required field: {field}")
            elif manifest[field] != expected_value:
                self.result.fail("manifest.json", f"{field} should be {expected_value!r}, got {manifest[field]!r}")
            else:
                self.result.ok(f"manifest.json '{field}' is correct")

        # Check other recommended fields
        recommended_fields = ["version", "codeowners", "documentation", "iot_class"]
        for field in recommended_fields:
            if field in manifest:
                self.result.ok(f"manifest.json has '{field}' field")
            else:
                self.result.fail("manifest.json", f"Recommended field '{field}' missing")


class TestConstValues:
    """Test that const.py has correct values."""

    def __init__(self, result: TestResult):
        self.result = result

    def run(self) -> None:
        """Run const.py tests."""
        print("\n9. Testing Constants")
        print("-" * 40)

        module = load_module_ast(COMPONENTS_PATH / "const.py")

        # Expected constants
        expected_constants = [
            "DOMAIN",
            "CONF_USE_HTTPS",
            "DEFAULT_NAME",
            "DEFAULT_PORT",
            "UPDATE_INTERVAL",
            "SERVICE_LOAD_URL",
            "SERVICE_EXECUTE_JS",
            "SERVICE_SEND_CEC",
            "SERVICE_CLEAR_DATA",
            "SERVICE_SET_ZOOM",
            "ATTR_URL",
            "ATTR_SCRIPT",
            "ATTR_COMMAND",
            "ATTR_DATA_TYPE",
            "ATTR_LEVEL",
            "CEC_COMMANDS",
            "HDMI_INPUTS",
            "SESSION_MODES",
            "CLEAR_DATA_TYPES",
        ]

        defined_constants = []
        for node in module.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        defined_constants.append(target.id)
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                defined_constants.append(node.target.id)

        missing = [c for c in expected_constants if c not in defined_constants]
        if missing:
            self.result.fail("Constants", f"Missing: {missing}")
        else:
            self.result.ok(f"All {len(expected_constants)} expected constants defined")


class TestEntityBase:
    """Test the base entity class."""

    def __init__(self, result: TestResult):
        self.result = result

    def run(self) -> None:
        """Run entity.py tests."""
        print("\n10. Testing Base Entity")
        print("-" * 40)

        module = load_module_ast(COMPONENTS_PATH / "entity.py")

        classes = get_class_names(module)
        if "ScreenPilotEntity" not in classes:
            self.result.fail("Base Entity", "ScreenPilotEntity class not found")
            return

        self.result.ok("ScreenPilotEntity class defined")

        # Check for required properties
        properties_found = {"device_info": False, "data": False}

        for node in ast.walk(module):
            if isinstance(node, ast.ClassDef) and node.name == "ScreenPilotEntity":
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        for decorator in item.decorator_list:
                            if isinstance(decorator, ast.Name) and decorator.id == "property":
                                if item.name in properties_found:
                                    properties_found[item.name] = True

        for prop, found in properties_found.items():
            if found:
                self.result.ok(f"ScreenPilotEntity.{prop} property defined")
            else:
                self.result.fail("Base Entity", f"{prop} property not found")


def main() -> int:
    """Run all tests."""
    print("=" * 60)
    print("ScreenPilot Home Assistant Integration Validator")
    print("=" * 60)

    if YAML_AVAILABLE:
        print("(Using PyYAML for YAML parsing)")
    else:
        print("(Using basic YAML parser - install pyyaml for full validation)")

    result = TestResult()

    # Run all test suites
    TestModuleImports(result).run()
    TestEntityDescriptions(result).run()
    TestCoordinatorDataClass(result).run()
    TestAPIClient(result).run()
    TestConfigFlow(result).run()
    TestServicesYAML(result).run()
    TestInitSetup(result).run()
    TestManifest(result).run()
    TestConstValues(result).run()
    TestEntityBase(result).run()

    # Print summary
    success = result.summary()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
