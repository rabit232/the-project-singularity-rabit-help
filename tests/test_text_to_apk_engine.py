#!/usr/bin/env python3
"""
Comprehensive Test Suite for Project Singularity Text-to-APK Engine
Tests all components of the AI-powered APK generation system
"""

import pytest
import asyncio
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.text_to_apk_engine import TextToAPKEngine, AppSpecification, AppFramework, AppCategory
from core.ai_engine.prompt_engineer import PromptEngineer, AIModel, PromptType
from core.builders.react_native_builder import ReactNativeBuilder

class TestTextToAPKEngine:
    """Test suite for the main Text-to-APK engine"""
    
    @pytest.fixture
    def engine(self):
        """Create a test engine instance"""
        return TextToAPKEngine()
    
    @pytest.fixture
    def sample_app_spec(self):
        """Sample app specification for testing"""
        return AppSpecification(
            name="Test Calculator App",
            description="A simple calculator with basic arithmetic operations",
            category=AppCategory.UTILITY,
            framework=AppFramework.REACT_NATIVE,
            features=["addition", "subtraction", "multiplication", "division"],
            ui_style="modern",
            target_audience="general users",
            complexity_level=3,
            api_integrations=[],
            permissions=["INTERNET"]
        )
    
    @pytest.mark.asyncio
    async def test_generate_apk_from_text_success(self, engine):
        """Test successful APK generation from text prompt"""
        prompt = "Create a simple calculator app with basic arithmetic operations"
        
        with patch.object(engine, 'analyze_prompt') as mock_analyze, \
             patch.object(engine, 'generate_architecture') as mock_arch, \
             patch.object(engine, 'generate_source_code') as mock_code, \
             patch.object(engine, 'build_apk') as mock_build:
            
            # Mock responses
            mock_analyze.return_value = AppSpecification(
                name="Calculator App",
                description="Simple calculator",
                category=AppCategory.UTILITY,
                framework=AppFramework.REACT_NATIVE,
                features=["arithmetic"],
                ui_style="modern",
                target_audience="general",
                complexity_level=3,
                api_integrations=[],
                permissions=["INTERNET"]
            )
            
            mock_arch.return_value = {"components": ["Calculator"], "screens": ["Main"]}
            mock_code.return_value = {"App.js": "mock code"}
            mock_build.return_value = {
                "apk_path": "/mock/path/app.apk",
                "build_logs": ["Build successful"],
                "build_time": 120
            }
            
            result = await engine.generate_apk_from_text(prompt)
            
            assert result["success"] is True
            assert "app_specification" in result
            assert "apk_path" in result
            assert "metadata" in result
            
            # Verify all methods were called
            mock_analyze.assert_called_once()
            mock_arch.assert_called_once()
            mock_code.assert_called_once()
            mock_build.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_apk_from_text_failure(self, engine):
        """Test APK generation failure handling"""
        prompt = "Invalid prompt"
        
        with patch.object(engine, 'analyze_prompt') as mock_analyze:
            mock_analyze.side_effect = Exception("Analysis failed")
            
            result = await engine.generate_apk_from_text(prompt)
            
            assert result["success"] is False
            assert "error" in result
    
    def test_fallback_prompt_analysis(self, engine):
        """Test fallback prompt analysis when AI is unavailable"""
        prompt = "Create a todo list app with categories"
        
        result = engine._fallback_prompt_analysis(prompt, None)
        
        assert isinstance(result, AppSpecification)
        assert result.name is not None
        assert result.category in [cat for cat in AppCategory]
        assert result.framework in [fw for fw in AppFramework]
    
    def test_extract_features(self, engine):
        """Test feature extraction from prompts"""
        prompt = "Create an app with camera, GPS location, and push notifications"
        
        features = engine._extract_features(prompt)
        
        assert "camera" in features
        assert "location" in features
        assert "notifications" in features
    
    def test_get_template_architecture(self, engine, sample_app_spec):
        """Test template architecture generation"""
        architecture = engine._get_template_architecture(sample_app_spec)
        
        assert "components" in architecture
        assert "screens" in architecture
        assert "navigation" in architecture
        assert isinstance(architecture["components"], list)
        assert len(architecture["components"]) > 0

class TestPromptEngineer:
    """Test suite for the AI prompt engineering system"""
    
    @pytest.fixture
    def prompt_engineer(self):
        """Create a test prompt engineer instance"""
        return PromptEngineer()
    
    @pytest.mark.asyncio
    async def test_analyze_app_prompt_success(self, prompt_engineer):
        """Test successful app prompt analysis"""
        prompt = "Create a weather app with 5-day forecast"
        
        with patch.object(prompt_engineer, '_execute_prompt') as mock_execute:
            mock_response = Mock()
            mock_response.content = json.dumps({
                "name": "Weather App",
                "description": "Weather application with forecasts",
                "category": "weather",
                "framework": "react_native",
                "features": ["weather_api", "forecast"],
                "ui_style": "modern",
                "target_audience": "general users",
                "complexity_level": 5,
                "api_integrations": ["weather_api"],
                "permissions": ["INTERNET", "LOCATION"]
            })
            mock_response.model = AIModel.GPT_4
            mock_response.response_time = 2.5
            mock_response.confidence_score = 0.9
            mock_execute.return_value = mock_response
            
            result = await prompt_engineer.analyze_app_prompt(prompt)
            
            assert result["success"] is True
            assert result["app_specification"]["name"] == "Weather App"
            assert result["app_specification"]["category"] == "weather"
            assert "ai_metadata" in result
    
    @pytest.mark.asyncio
    async def test_analyze_app_prompt_invalid_json(self, prompt_engineer):
        """Test handling of invalid JSON response"""
        prompt = "Create an app"
        
        with patch.object(prompt_engineer, '_execute_prompt') as mock_execute:
            mock_response = Mock()
            mock_response.content = "Invalid JSON response"
            mock_response.model = AIModel.GPT_4
            mock_response.response_time = 1.0
            mock_execute.return_value = mock_response
            
            result = await prompt_engineer.analyze_app_prompt(prompt)
            
            assert result["success"] is False
            assert "error" in result
            assert "raw_response" in result
    
    @pytest.mark.asyncio
    async def test_generate_architecture(self, prompt_engineer):
        """Test architecture generation"""
        app_spec = {
            "name": "Test App",
            "framework": "react_native",
            "complexity_level": 5,
            "features": ["navigation", "api"]
        }
        
        with patch.object(prompt_engineer, '_execute_prompt') as mock_execute:
            mock_response = Mock()
            mock_response.content = json.dumps({
                "components": ["Header", "Navigation", "Content"],
                "screens": ["Home", "Settings"],
                "navigation": {"type": "stack"},
                "data_flow": "redux"
            })
            mock_response.model = AIModel.GPT_4
            mock_response.response_time = 3.0
            mock_execute.return_value = mock_response
            
            result = await prompt_engineer.generate_architecture(app_spec)
            
            assert result["success"] is True
            assert "architecture" in result
            assert len(result["architecture"]["components"]) == 3
    
    def test_calculate_confidence_valid_json(self, prompt_engineer):
        """Test confidence calculation for valid JSON"""
        template = Mock()
        template.type = PromptType.ANALYSIS
        template.constraints = {"required_fields": ["name", "category"]}
        
        valid_json = '{"name": "Test App", "category": "utility"}'
        confidence = prompt_engineer._calculate_confidence(valid_json, template)
        
        assert confidence >= 0.8
        assert confidence <= 1.0
    
    def test_calculate_confidence_invalid_json(self, prompt_engineer):
        """Test confidence calculation for invalid JSON"""
        template = Mock()
        template.type = PromptType.ANALYSIS
        
        invalid_json = "This is not JSON"
        confidence = prompt_engineer._calculate_confidence(invalid_json, template)
        
        assert confidence == 0.3
    
    def test_validate_app_specification(self, prompt_engineer):
        """Test app specification validation"""
        invalid_spec = {
            "name": "Test App",
            "category": "invalid_category",
            "framework": "invalid_framework"
        }
        
        validated_spec = prompt_engineer._validate_app_specification(invalid_spec)
        
        assert validated_spec["category"] == "utility"  # Default fallback
        assert validated_spec["framework"] == "react_native"  # Default fallback
        assert "description" in validated_spec
        assert "features" in validated_spec

class TestReactNativeBuilder:
    """Test suite for the React Native builder"""
    
    @pytest.fixture
    def builder(self):
        """Create a test React Native builder"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield ReactNativeBuilder(build_dir=Path(temp_dir))
    
    @pytest.fixture
    def sample_app_spec(self):
        """Sample app specification for testing"""
        return {
            "name": "Test React Native App",
            "description": "A test application",
            "category": "utility",
            "framework": "react_native",
            "features": ["navigation", "storage"],
            "complexity_level": 4
        }
    
    @pytest.fixture
    def sample_architecture(self):
        """Sample architecture for testing"""
        return {
            "components": ["Header", "Navigation", "Content"],
            "screens": ["Home", "Settings"],
            "navigation": {"type": "stack"},
            "data_flow": "context"
        }
    
    @pytest.mark.asyncio
    async def test_generate_complete_project(self, builder, sample_app_spec, sample_architecture):
        """Test complete project generation"""
        result = await builder.generate_complete_project(sample_app_spec, sample_architecture)
        
        assert result["success"] is True
        assert "project_path" in result
        assert "files_generated" in result
        assert result["build_ready"] is True
        
        # Verify project structure exists
        project_path = Path(result["project_path"])
        assert project_path.exists()
        assert (project_path / "package.json").exists()
        assert (project_path / "src/App.tsx").exists()
    
    @pytest.mark.asyncio
    async def test_generate_core_files(self, builder, sample_app_spec):
        """Test core files generation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            files = await builder._generate_core_files(project_path, sample_app_spec)
            
            assert "package.json" in files
            assert "index.js" in files
            assert "app.json" in files
            
            # Verify package.json content
            with open(project_path / "package.json") as f:
                package_data = json.load(f)
            
            assert package_data["name"] == builder._sanitize_project_name(sample_app_spec["name"])
            assert "react-native" in package_data["dependencies"]
    
    @pytest.mark.asyncio
    async def test_generate_source_files(self, builder, sample_app_spec, sample_architecture):
        """Test source files generation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            (project_path / "src/screens").mkdir(parents=True)
            
            files = await builder._generate_source_files(project_path, sample_app_spec, sample_architecture)
            
            assert "src/App.tsx" in files
            assert "src/screens/HomeScreen.tsx" in files
            assert "src/screens/SettingsScreen.tsx" in files
            
            # Verify App.tsx exists and contains expected content
            app_file = project_path / "src/App.tsx"
            assert app_file.exists()
            
            with open(app_file) as f:
                content = f.read()
            
            assert sample_app_spec["name"] in content
            assert "NavigationContainer" in content
    
    @pytest.mark.asyncio
    async def test_build_apk_success(self, builder, sample_app_spec):
        """Test successful APK building"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Create minimal project structure
            (project_path / "android/app/build/outputs/apk/debug").mkdir(parents=True)
            
            with patch.object(builder, '_install_dependencies') as mock_install, \
                 patch.object(builder, '_build_android_apk') as mock_build:
                
                mock_apk_path = project_path / "test.apk"
                mock_build.return_value = mock_apk_path
                
                result = await builder.build_apk(str(project_path), sample_app_spec)
                
                assert result["success"] is True
                assert "apk_path" in result
                assert "build_time" in result
                assert "build_logs" in result
                
                mock_install.assert_called_once()
                mock_build.assert_called_once()
    
    def test_sanitize_project_name(self, builder):
        """Test project name sanitization"""
        test_cases = [
            ("My App Name", "MyAppName"),
            ("App with 123 numbers", "Appwith123numbers"),
            ("Special!@#$%Characters", "SpecialCharacters"),
            ("123StartWithNumber", "App123StartWithNumber"),
            ("", "GeneratedApp")
        ]
        
        for input_name, expected in test_cases:
            result = builder._sanitize_project_name(input_name)
            assert result == expected
    
    def test_get_build_logs(self, builder):
        """Test build logs retrieval"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            logs = builder._get_build_logs(project_path)
            
            assert isinstance(logs, list)
            assert len(logs) > 0
            assert any("build" in log.lower() for log in logs)

class TestIntegration:
    """Integration tests for the complete system"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_apk_generation(self):
        """Test complete end-to-end APK generation"""
        engine = TextToAPKEngine()
        prompt = "Create a simple note-taking app with categories"
        
        with patch.object(engine, 'openai_client') as mock_openai:
            # Mock OpenAI response
            mock_openai.ChatCompletion.acreate = AsyncMock(return_value=Mock(
                choices=[Mock(message=Mock(content=json.dumps({
                    "name": "Notes App",
                    "description": "Simple note-taking application",
                    "category": "productivity",
                    "framework": "react_native",
                    "features": ["notes", "categories", "search"],
                    "ui_style": "clean",
                    "target_audience": "students",
                    "complexity_level": 4,
                    "api_integrations": [],
                    "permissions": ["WRITE_EXTERNAL_STORAGE"]
                })))],
                usage=Mock(total_tokens=500)
            ))
            
            with patch('core.builders.react_native_builder.ReactNativeBuilder') as mock_builder_class:
                mock_builder = Mock()
                mock_builder_class.return_value = mock_builder
                
                mock_builder.generate_code.return_value = {
                    "files": {"App.js": "mock code"},
                    "dependencies": ["react", "react-native"]
                }
                
                mock_builder.build_apk.return_value = {
                    "apk_path": "/mock/notes-app.apk",
                    "build_logs": ["Build successful"],
                    "build_time": 180
                }
                
                result = await engine.generate_apk_from_text(prompt)
                
                # Verify successful generation
                assert result["success"] is True
                assert result["app_specification"]["name"] == "Notes App"
                assert result["app_specification"]["category"] == "productivity"
    
    @pytest.mark.asyncio
    async def test_multiple_framework_support(self):
        """Test support for multiple frameworks"""
        engine = TextToAPKEngine()
        
        frameworks_to_test = [
            AppFramework.REACT_NATIVE,
            AppFramework.FLUTTER,
            AppFramework.KIVY,
            AppFramework.CORDOVA
        ]
        
        for framework in frameworks_to_test:
            app_spec = AppSpecification(
                name=f"Test {framework.value} App",
                description="Test application",
                category=AppCategory.UTILITY,
                framework=framework,
                features=["basic_ui"],
                ui_style="modern",
                target_audience="general",
                complexity_level=3,
                api_integrations=[],
                permissions=["INTERNET"]
            )
            
            # Test that each framework has a builder
            assert framework in engine.framework_builders
            
            builder = engine.framework_builders[framework]
            assert hasattr(builder, 'generate_code')
            assert hasattr(builder, 'build_apk')

class TestPerformance:
    """Performance tests for the system"""
    
    @pytest.mark.asyncio
    async def test_concurrent_generations(self):
        """Test handling of concurrent APK generations"""
        engine = TextToAPKEngine()
        
        prompts = [
            "Create a calculator app",
            "Create a weather app",
            "Create a todo app",
            "Create a notes app",
            "Create a timer app"
        ]
        
        with patch.object(engine, 'analyze_prompt') as mock_analyze, \
             patch.object(engine, 'generate_architecture') as mock_arch, \
             patch.object(engine, 'generate_source_code') as mock_code, \
             patch.object(engine, 'build_apk') as mock_build:
            
            # Mock quick responses
            mock_analyze.return_value = AppSpecification(
                name="Test App", description="Test", category=AppCategory.UTILITY,
                framework=AppFramework.REACT_NATIVE, features=[], ui_style="modern",
                target_audience="general", complexity_level=3, api_integrations=[], permissions=[]
            )
            mock_arch.return_value = {"components": [], "screens": []}
            mock_code.return_value = {"App.js": "code"}
            mock_build.return_value = {"apk_path": "/test.apk", "build_logs": [], "build_time": 1}
            
            # Run concurrent generations
            tasks = [engine.generate_apk_from_text(prompt) for prompt in prompts]
            results = await asyncio.gather(*tasks)
            
            # Verify all succeeded
            assert len(results) == len(prompts)
            assert all(result["success"] for result in results)
    
    def test_memory_usage(self):
        """Test memory usage during generation"""
        import psutil
        import gc
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        # Create multiple engine instances
        engines = [TextToAPKEngine() for _ in range(10)]
        
        # Force garbage collection
        gc.collect()
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB for 10 instances)
        assert memory_increase < 100 * 1024 * 1024  # 100MB

# Test fixtures and utilities
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )

# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
