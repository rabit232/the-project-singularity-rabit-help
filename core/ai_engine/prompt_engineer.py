#!/usr/bin/env python3
"""
Advanced AI Prompt Engineering System for Project Singularity
Sophisticated prompt construction, optimization, and multi-model orchestration
"""

import json
import asyncio
import logging
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import openai
from pathlib import Path
import re
import hashlib
import time

logger = logging.getLogger(__name__)

class AIModel(Enum):
    """Supported AI models for different tasks"""
    GPT_4_TURBO = "gpt-4-turbo-preview"
    GPT_4 = "gpt-4"
    GPT_3_5_TURBO = "gpt-3.5-turbo"
    CLAUDE_3_OPUS = "claude-3-opus"
    CLAUDE_3_SONNET = "claude-3-sonnet"
    GEMINI_PRO = "gemini-pro"

class PromptType(Enum):
    """Different types of prompts for specialized tasks"""
    ANALYSIS = "analysis"
    ARCHITECTURE = "architecture"
    CODE_GENERATION = "code_generation"
    OPTIMIZATION = "optimization"
    TESTING = "testing"
    DOCUMENTATION = "documentation"

@dataclass
class PromptTemplate:
    """Structured prompt template with variables and constraints"""
    name: str
    type: PromptType
    template: str
    variables: List[str]
    constraints: Dict[str, Any]
    model_preferences: List[AIModel]
    max_tokens: int = 2000
    temperature: float = 0.7
    examples: Optional[List[Dict[str, str]]] = None

@dataclass
class AIResponse:
    """Structured AI response with metadata"""
    content: str
    model: AIModel
    prompt_hash: str
    tokens_used: int
    response_time: float
    confidence_score: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

class PromptEngineer:
    """
    Advanced prompt engineering system with multi-model orchestration
    """
    
    def __init__(self, openai_api_key: Optional[str] = None):
        self.openai_client = None
        if openai_api_key:
            openai.api_key = openai_api_key
            self.openai_client = openai
        
        self.templates_cache = {}
        self.response_cache = {}
        self.load_prompt_templates()
    
    def load_prompt_templates(self):
        """Load and cache prompt templates"""
        templates_dir = Path(__file__).parent / "templates"
        templates_dir.mkdir(exist_ok=True)
        
        # Analysis Templates
        self.templates_cache["app_analysis"] = PromptTemplate(
            name="app_analysis",
            type=PromptType.ANALYSIS,
            template="""
You are an expert mobile app analyst. Analyze the following app description and extract structured information.

User Request: "{prompt}"
User Preferences: {preferences}

Extract and return a JSON object with these fields:
- name: App name (generate creative name if not specified)
- description: Detailed app description (expand on user input)
- category: One of [productivity, utility, entertainment, business, education, social, health, finance, travel, shopping, news, photography, music, sports, weather, food, lifestyle]
- framework: Recommended framework based on requirements [react_native, flutter, kivy, cordova, native_android]
- features: List of main features (be comprehensive)
- ui_style: UI/UX style description (modern, minimalist, colorful, professional, etc.)
- target_audience: Target user demographic
- complexity_level: Complexity on 1-10 scale
- api_integrations: Required external APIs
- permissions: Required Android permissions
- monetization: Suggested monetization strategy
- similar_apps: List of similar existing apps for reference
- unique_selling_points: What makes this app special
- technical_requirements: Special technical considerations

Consider these factors:
1. App complexity and required features
2. Target audience and use case
3. Performance requirements
4. Development timeline
5. Maintenance considerations

Respond with valid JSON only. Be thorough and creative while staying practical.
            """,
            variables=["prompt", "preferences"],
            constraints={
                "max_features": 15,
                "min_features": 3,
                "valid_categories": ["productivity", "utility", "entertainment", "business", "education", "social", "health", "finance", "travel", "shopping", "news", "photography", "music", "sports", "weather", "food", "lifestyle"],
                "valid_frameworks": ["react_native", "flutter", "kivy", "cordova", "native_android"]
            },
            model_preferences=[AIModel.GPT_4_TURBO, AIModel.GPT_4, AIModel.CLAUDE_3_OPUS],
            max_tokens=3000,
            temperature=0.8
        )
        
        # Architecture Templates
        self.templates_cache["app_architecture"] = PromptTemplate(
            name="app_architecture",
            type=PromptType.ARCHITECTURE,
            template="""
You are a senior software architect specializing in mobile applications. Design a comprehensive architecture for the following app:

App Specification:
{app_spec}

Framework: {framework}
Complexity Level: {complexity}/10

Design a detailed application architecture and return a JSON object with:

- components: List of UI components with descriptions
- screens: List of app screens/pages with navigation flow
- navigation: Navigation structure and routing
- data_flow: Data management approach (state management, local storage, etc.)
- external_services: Required external integrations and APIs
- file_structure: Recommended project file/folder structure
- dependencies: Required packages and libraries
- database_schema: If data persistence is needed
- api_endpoints: If backend services are required
- security_considerations: Security measures and best practices
- performance_optimizations: Performance enhancement strategies
- testing_strategy: Recommended testing approach
- deployment_considerations: Build and deployment requirements

Consider these architectural principles:
1. Scalability and maintainability
2. Performance optimization
3. Security best practices
4. User experience optimization
5. Code reusability
6. Framework-specific best practices

Provide detailed, production-ready architecture. Return valid JSON only.
            """,
            variables=["app_spec", "framework", "complexity"],
            constraints={
                "min_components": 5,
                "min_screens": 2,
                "max_screens": 20
            },
            model_preferences=[AIModel.GPT_4_TURBO, AIModel.CLAUDE_3_OPUS],
            max_tokens=4000,
            temperature=0.6
        )
        
        # Code Generation Templates
        self.templates_cache["code_generation"] = PromptTemplate(
            name="code_generation",
            type=PromptType.CODE_GENERATION,
            template="""
You are an expert {framework} developer. Generate production-ready code for the following specification:

App Specification:
{app_spec}

Architecture:
{architecture}

Component to Generate: {component}

Generate complete, production-ready code with:
1. Proper error handling
2. Type safety (where applicable)
3. Performance optimizations
4. Accessibility features
5. Responsive design
6. Clean, maintainable code structure
7. Comprehensive comments
8. Best practices for {framework}

Include:
- Main component/screen code
- Styling/CSS (if applicable)
- State management
- API integration (if needed)
- Navigation setup
- Testing utilities

Return a JSON object with:
- files: Dictionary of filename -> file content
- dependencies: List of required packages
- setup_instructions: Step-by-step setup guide
- testing_notes: How to test the component
- optimization_notes: Performance considerations

Focus on code quality, maintainability, and following {framework} best practices.
            """,
            variables=["framework", "app_spec", "architecture", "component"],
            constraints={
                "min_files": 1,
                "max_files": 10
            },
            model_preferences=[AIModel.GPT_4_TURBO, AIModel.GPT_4],
            max_tokens=6000,
            temperature=0.4
        )
    
    async def analyze_app_prompt(self, prompt: str, user_preferences: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Analyze user prompt and extract comprehensive app specification
        """
        template = self.templates_cache["app_analysis"]
        
        # Prepare variables
        variables = {
            "prompt": prompt,
            "preferences": json.dumps(user_preferences or {}, indent=2)
        }
        
        # Generate and execute prompt
        response = await self._execute_prompt(template, variables)
        
        try:
            # Parse JSON response
            app_spec = json.loads(response.content)
            
            # Validate and enhance response
            app_spec = self._validate_app_specification(app_spec)
            
            return {
                "success": True,
                "app_specification": app_spec,
                "ai_metadata": {
                    "model": response.model.value,
                    "confidence": response.confidence_score,
                    "response_time": response.response_time
                }
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            return {
                "success": False,
                "error": "Invalid AI response format",
                "raw_response": response.content
            }
    
    async def generate_architecture(self, app_spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive application architecture
        """
        template = self.templates_cache["app_architecture"]
        
        variables = {
            "app_spec": json.dumps(app_spec, indent=2),
            "framework": app_spec.get("framework", "react_native"),
            "complexity": app_spec.get("complexity_level", 5)
        }
        
        response = await self._execute_prompt(template, variables)
        
        try:
            architecture = json.loads(response.content)
            
            # Enhance architecture with framework-specific details
            architecture = self._enhance_architecture(architecture, app_spec)
            
            return {
                "success": True,
                "architecture": architecture,
                "ai_metadata": {
                    "model": response.model.value,
                    "response_time": response.response_time
                }
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse architecture response: {e}")
            return {
                "success": False,
                "error": "Invalid architecture response",
                "raw_response": response.content
            }
    
    async def generate_code_component(self, app_spec: Dict[str, Any], architecture: Dict[str, Any], component: str) -> Dict[str, Any]:
        """
        Generate code for a specific component
        """
        template = self.templates_cache["code_generation"]
        
        variables = {
            "framework": app_spec.get("framework", "react_native"),
            "app_spec": json.dumps(app_spec, indent=2),
            "architecture": json.dumps(architecture, indent=2),
            "component": component
        }
        
        response = await self._execute_prompt(template, variables)
        
        try:
            code_result = json.loads(response.content)
            
            return {
                "success": True,
                "code": code_result,
                "ai_metadata": {
                    "model": response.model.value,
                    "response_time": response.response_time
                }
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse code generation response: {e}")
            return {
                "success": False,
                "error": "Invalid code generation response",
                "raw_response": response.content
            }
    
    async def _execute_prompt(self, template: PromptTemplate, variables: Dict[str, Any]) -> AIResponse:
        """
        Execute a prompt with the best available AI model
        """
        # Format prompt with variables
        formatted_prompt = template.template.format(**variables)
        
        # Generate prompt hash for caching
        prompt_hash = hashlib.md5(formatted_prompt.encode()).hexdigest()
        
        # Check cache
        if prompt_hash in self.response_cache:
            return self.response_cache[prompt_hash]
        
        # Try models in order of preference
        for model in template.model_preferences:
            try:
                start_time = time.time()
                
                if model in [AIModel.GPT_4_TURBO, AIModel.GPT_4, AIModel.GPT_3_5_TURBO]:
                    response = await self._call_openai(
                        model=model.value,
                        prompt=formatted_prompt,
                        max_tokens=template.max_tokens,
                        temperature=template.temperature
                    )
                else:
                    # Fallback for other models
                    response = await self._call_fallback_model(formatted_prompt, template)
                
                response_time = time.time() - start_time
                
                ai_response = AIResponse(
                    content=response["content"],
                    model=model,
                    prompt_hash=prompt_hash,
                    tokens_used=response.get("tokens_used", 0),
                    response_time=response_time,
                    confidence_score=self._calculate_confidence(response["content"], template)
                )
                
                # Cache successful response
                self.response_cache[prompt_hash] = ai_response
                
                return ai_response
                
            except Exception as e:
                logger.warning(f"Model {model.value} failed: {e}")
                continue
        
        # If all models fail, raise exception
        raise Exception("All AI models failed to respond")
    
    async def _call_openai(self, model: str, prompt: str, max_tokens: int, temperature: float) -> Dict[str, Any]:
        """
        Call OpenAI API with error handling
        """
        if not self.openai_client:
            raise Exception("OpenAI client not initialized")
        
        try:
            response = await self.openai_client.ChatCompletion.acreate(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert mobile app developer and architect. Provide detailed, accurate, and production-ready responses."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=0.9,
                frequency_penalty=0.1,
                presence_penalty=0.1
            )
            
            return {
                "content": response.choices[0].message.content,
                "tokens_used": response.usage.total_tokens
            }
            
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise
    
    async def _call_fallback_model(self, prompt: str, template: PromptTemplate) -> Dict[str, Any]:
        """
        Fallback model implementation (local or alternative API)
        """
        # This would integrate with other AI providers or local models
        # For now, return a structured fallback response
        
        if template.type == PromptType.ANALYSIS:
            return {
                "content": json.dumps({
                    "name": "Generated App",
                    "description": "A mobile application generated from user prompt",
                    "category": "utility",
                    "framework": "react_native",
                    "features": ["basic_ui", "data_display"],
                    "ui_style": "modern",
                    "target_audience": "general users",
                    "complexity_level": 5,
                    "api_integrations": [],
                    "permissions": ["INTERNET"],
                    "monetization": "free",
                    "similar_apps": [],
                    "unique_selling_points": ["AI-generated", "customizable"],
                    "technical_requirements": ["standard mobile device"]
                }),
                "tokens_used": 500
            }
        
        # Add more fallback responses for other prompt types
        return {
            "content": "Fallback response - please configure AI models properly",
            "tokens_used": 100
        }
    
    def _calculate_confidence(self, response: str, template: PromptTemplate) -> float:
        """
        Calculate confidence score for AI response
        """
        try:
            # For JSON responses, check if valid JSON
            if template.type in [PromptType.ANALYSIS, PromptType.ARCHITECTURE]:
                json.loads(response)
                confidence = 0.8  # Base confidence for valid JSON
                
                # Check for required fields based on template constraints
                if template.constraints:
                    # Add logic to validate required fields
                    confidence += 0.1
                
                return min(confidence, 1.0)
            
            # For code generation, check for basic code structure
            elif template.type == PromptType.CODE_GENERATION:
                if any(keyword in response.lower() for keyword in ["function", "class", "import", "export"]):
                    return 0.7
                return 0.5
            
            return 0.6  # Default confidence
            
        except:
            return 0.3  # Low confidence for invalid responses
    
    def _validate_app_specification(self, app_spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and enhance app specification
        """
        # Ensure required fields exist
        required_fields = ["name", "description", "category", "framework", "features"]
        for field in required_fields:
            if field not in app_spec:
                app_spec[field] = self._get_default_value(field)
        
        # Validate category
        valid_categories = ["productivity", "utility", "entertainment", "business", "education", "social", "health", "finance", "travel", "shopping", "news", "photography", "music", "sports", "weather", "food", "lifestyle"]
        if app_spec["category"] not in valid_categories:
            app_spec["category"] = "utility"
        
        # Validate framework
        valid_frameworks = ["react_native", "flutter", "kivy", "cordova", "native_android"]
        if app_spec["framework"] not in valid_frameworks:
            app_spec["framework"] = "react_native"
        
        # Ensure complexity level is within range
        if "complexity_level" not in app_spec or not isinstance(app_spec["complexity_level"], int):
            app_spec["complexity_level"] = 5
        app_spec["complexity_level"] = max(1, min(10, app_spec["complexity_level"]))
        
        return app_spec
    
    def _enhance_architecture(self, architecture: Dict[str, Any], app_spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance architecture with framework-specific details
        """
        framework = app_spec.get("framework", "react_native")
        
        # Add framework-specific enhancements
        if framework == "react_native":
            architecture["build_config"] = {
                "metro_config": True,
                "babel_config": True,
                "typescript": True
            }
        elif framework == "flutter":
            architecture["build_config"] = {
                "pubspec_yaml": True,
                "dart_analysis": True,
                "material_design": True
            }
        elif framework == "kivy":
            architecture["build_config"] = {
                "buildozer_spec": True,
                "python_requirements": True,
                "kv_files": True
            }
        
        return architecture
    
    def _get_default_value(self, field: str) -> Any:
        """
        Get default value for missing fields
        """
        defaults = {
            "name": "Generated App",
            "description": "A mobile application",
            "category": "utility",
            "framework": "react_native",
            "features": ["basic_ui"],
            "ui_style": "modern",
            "target_audience": "general users",
            "complexity_level": 5,
            "api_integrations": [],
            "permissions": ["INTERNET"]
        }
        return defaults.get(field, "")

# Advanced prompt optimization utilities
class PromptOptimizer:
    """
    Optimize prompts for better AI responses
    """
    
    @staticmethod
    def optimize_for_json_output(prompt: str) -> str:
        """
        Optimize prompt for JSON output
        """
        if "json" not in prompt.lower():
            prompt += "\n\nIMPORTANT: Respond with valid JSON only. Do not include any explanatory text outside the JSON structure."
        
        return prompt
    
    @staticmethod
    def add_examples(prompt: str, examples: List[Dict[str, str]]) -> str:
        """
        Add examples to improve prompt quality
        """
        if not examples:
            return prompt
        
        examples_text = "\n\nExamples:\n"
        for i, example in enumerate(examples, 1):
            examples_text += f"\nExample {i}:\n"
            examples_text += f"Input: {example.get('input', '')}\n"
            examples_text += f"Output: {example.get('output', '')}\n"
        
        return prompt + examples_text
    
    @staticmethod
    def add_constraints(prompt: str, constraints: Dict[str, Any]) -> str:
        """
        Add constraints to prompt for better control
        """
        if not constraints:
            return prompt
        
        constraints_text = "\n\nConstraints:\n"
        for key, value in constraints.items():
            constraints_text += f"- {key}: {value}\n"
        
        return prompt + constraints_text

# Example usage and testing
if __name__ == "__main__":
    async def test_prompt_engineer():
        engineer = PromptEngineer()
        
        # Test app analysis
        test_prompt = "Create a fitness tracking app with workout plans and progress tracking"
        result = await engineer.analyze_app_prompt(test_prompt)
        
        if result["success"]:
            print("✅ App Analysis Success:")
            print(json.dumps(result["app_specification"], indent=2))
            
            # Test architecture generation
            arch_result = await engineer.generate_architecture(result["app_specification"])
            
            if arch_result["success"]:
                print("\n✅ Architecture Generation Success:")
                print(json.dumps(arch_result["architecture"], indent=2))
        else:
            print(f"❌ Analysis Failed: {result['error']}")
    
    # Run test
    asyncio.run(test_prompt_engineer())
