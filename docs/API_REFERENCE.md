# Project Singularity API Reference

## Overview

The Project Singularity API provides a comprehensive interface for AI-powered Android APK generation. Transform natural language descriptions into fully functional mobile applications through our advanced Text-to-APK engine.

## Base URL

```
Production: https://api.singularity.dev
Staging: https://staging-api.singularity.dev
Development: http://localhost:8000
```

## Authentication

All API requests require authentication using API keys:

```http
Authorization: Bearer YOUR_API_KEY
```

## Rate Limiting

- **Free Tier**: 10 requests per hour
- **Pro Tier**: 100 requests per hour  
- **Enterprise**: Unlimited requests

Rate limit headers are included in all responses:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

## Core Endpoints

### Generate APK from Text

Transform a natural language description into a complete Android APK.

```http
POST /api/v1/generate-apk
```

#### Request Body

```json
{
  "prompt": "Create a weather app with 5-day forecast and location detection",
  "preferences": {
    "framework": "react_native",
    "ui_style": "modern",
    "target_audience": "general users",
    "include_analytics": true,
    "monetization": "ads"
  },
  "options": {
    "build_type": "debug",
    "optimization_level": "standard",
    "include_source": false,
    "custom_package_name": "com.mycompany.weatherapp"
  }
}
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `prompt` | string | Yes | Natural language description of the desired app |
| `preferences` | object | No | User preferences for app generation |
| `preferences.framework` | enum | No | Target framework: `react_native`, `flutter`, `kivy`, `cordova`, `native_android` |
| `preferences.ui_style` | string | No | UI style preference: `modern`, `minimalist`, `colorful`, `professional` |
| `preferences.target_audience` | string | No | Target user demographic |
| `preferences.include_analytics` | boolean | No | Include analytics tracking (default: false) |
| `preferences.monetization` | enum | No | Monetization strategy: `free`, `ads`, `premium`, `freemium` |
| `options` | object | No | Advanced build options |
| `options.build_type` | enum | No | Build type: `debug`, `release` (default: debug) |
| `options.optimization_level` | enum | No | Optimization: `basic`, `standard`, `aggressive` (default: standard) |
| `options.include_source` | boolean | No | Include source code in response (default: false) |
| `options.custom_package_name` | string | No | Custom Android package name |

#### Response

```json
{
  "success": true,
  "generation_id": "gen_1234567890abcdef",
  "status": "processing",
  "estimated_completion": "2024-01-15T10:30:00Z",
  "app_specification": {
    "name": "Weather Forecast Pro",
    "description": "Advanced weather application with 5-day forecasts, location detection, and severe weather alerts",
    "category": "weather",
    "framework": "react_native",
    "features": [
      "current_weather",
      "5_day_forecast",
      "location_detection",
      "weather_alerts",
      "interactive_maps",
      "push_notifications"
    ],
    "ui_style": "modern",
    "target_audience": "general users",
    "complexity_level": 7,
    "api_integrations": [
      "openweathermap",
      "google_maps",
      "firebase_messaging"
    ],
    "permissions": [
      "INTERNET",
      "ACCESS_FINE_LOCATION",
      "ACCESS_COARSE_LOCATION",
      "RECEIVE_BOOT_COMPLETED"
    ],
    "monetization": "ads",
    "estimated_build_time": 180
  },
  "architecture": {
    "components": [
      "WeatherCard",
      "ForecastList", 
      "LocationPicker",
      "AlertsPanel",
      "SettingsScreen"
    ],
    "screens": [
      "HomeScreen",
      "ForecastScreen",
      "LocationScreen",
      "AlertsScreen",
      "SettingsScreen"
    ],
    "navigation": {
      "type": "tab_navigation",
      "structure": "bottom_tabs"
    },
    "data_flow": "redux_toolkit",
    "external_services": [
      {
        "name": "OpenWeatherMap API",
        "purpose": "Weather data",
        "endpoints": ["current", "forecast", "alerts"]
      }
    ]
  },
  "metadata": {
    "ai_model": "gpt-4-turbo",
    "confidence_score": 0.92,
    "processing_time": 3.2,
    "similar_apps": [
      "Weather Underground",
      "AccuWeather",
      "Weather Channel"
    ]
  }
}
```

### Check Generation Status

Monitor the progress of APK generation.

```http
GET /api/v1/generate-apk/{generation_id}/status
```

#### Response

```json
{
  "generation_id": "gen_1234567890abcdef",
  "status": "building",
  "progress": 65,
  "current_stage": "compiling_android_project",
  "stages": [
    {
      "name": "analyzing_prompt",
      "status": "completed",
      "duration": 2.1
    },
    {
      "name": "generating_architecture", 
      "status": "completed",
      "duration": 4.3
    },
    {
      "name": "generating_source_code",
      "status": "completed", 
      "duration": 12.7
    },
    {
      "name": "compiling_android_project",
      "status": "in_progress",
      "progress": 65
    },
    {
      "name": "signing_apk",
      "status": "pending"
    }
  ],
  "estimated_completion": "2024-01-15T10:28:00Z",
  "logs": [
    "2024-01-15T10:25:30Z - Starting React Native project generation",
    "2024-01-15T10:25:45Z - Installing dependencies: react-native@0.72.6",
    "2024-01-15T10:26:12Z - Generating weather components",
    "2024-01-15T10:26:30Z - Configuring API integrations"
  ]
}
```

### Download Generated APK

Download the completed APK file.

```http
GET /api/v1/generate-apk/{generation_id}/download
```

#### Response

Binary APK file with appropriate headers:

```http
Content-Type: application/vnd.android.package-archive
Content-Disposition: attachment; filename="weather-forecast-pro-v1.0.0.apk"
Content-Length: 15728640
```

### Get Source Code

Retrieve the generated source code (if enabled).

```http
GET /api/v1/generate-apk/{generation_id}/source
```

#### Response

```json
{
  "generation_id": "gen_1234567890abcdef",
  "framework": "react_native",
  "files": {
    "package.json": "{\n  \"name\": \"weather-forecast-pro\",\n  \"version\": \"1.0.0\",\n  ...",
    "src/App.tsx": "import React from 'react';\nimport {NavigationContainer} from '@react-navigation/native';\n...",
    "src/screens/HomeScreen.tsx": "import React, {useState, useEffect} from 'react';\n...",
    "android/app/build.gradle": "apply plugin: \"com.android.application\"\n..."
  },
  "project_structure": [
    "package.json",
    "src/App.tsx",
    "src/screens/HomeScreen.tsx",
    "src/screens/ForecastScreen.tsx",
    "src/components/WeatherCard.tsx",
    "src/services/WeatherAPI.ts",
    "android/app/build.gradle",
    "android/app/src/main/AndroidManifest.xml"
  ],
  "build_instructions": {
    "prerequisites": [
      "Node.js 18+",
      "React Native CLI",
      "Android Studio",
      "Java 17"
    ],
    "steps": [
      "npm install",
      "npx react-native run-android"
    ]
  }
}
```

## Template Management

### List Available Templates

Get a list of pre-built app templates.

```http
GET /api/v1/templates
```

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `category` | string | Filter by app category |
| `framework` | string | Filter by framework |
| `complexity` | integer | Filter by complexity level (1-10) |
| `limit` | integer | Number of results (default: 20, max: 100) |
| `offset` | integer | Pagination offset (default: 0) |

#### Response

```json
{
  "templates": [
    {
      "id": "template_weather_basic",
      "name": "Basic Weather App",
      "description": "Simple weather app with current conditions and 3-day forecast",
      "category": "weather",
      "framework": "react_native",
      "complexity_level": 4,
      "features": [
        "current_weather",
        "3_day_forecast",
        "location_detection"
      ],
      "preview_images": [
        "https://cdn.singularity.dev/templates/weather_basic_1.png",
        "https://cdn.singularity.dev/templates/weather_basic_2.png"
      ],
      "estimated_build_time": 120,
      "popularity_score": 8.7
    }
  ],
  "pagination": {
    "total": 156,
    "limit": 20,
    "offset": 0,
    "has_more": true
  }
}
```

### Generate from Template

Create an APK using a pre-built template.

```http
POST /api/v1/templates/{template_id}/generate
```

#### Request Body

```json
{
  "customizations": {
    "app_name": "My Weather App",
    "package_name": "com.mycompany.weather",
    "primary_color": "#2196F3",
    "api_keys": {
      "openweathermap": "your_api_key_here"
    },
    "features": {
      "push_notifications": true,
      "dark_mode": true,
      "premium_features": false
    }
  },
  "build_options": {
    "build_type": "release",
    "optimization_level": "aggressive"
  }
}
```

## User Management

### Get User Profile

Retrieve current user information and usage statistics.

```http
GET /api/v1/user/profile
```

#### Response

```json
{
  "user_id": "user_1234567890",
  "email": "developer@example.com",
  "plan": "pro",
  "usage": {
    "current_month": {
      "apk_generations": 23,
      "limit": 100,
      "reset_date": "2024-02-01T00:00:00Z"
    },
    "total": {
      "apk_generations": 156,
      "successful_builds": 142,
      "success_rate": 0.91
    }
  },
  "preferences": {
    "default_framework": "react_native",
    "default_ui_style": "modern",
    "include_analytics": false,
    "notification_email": true
  },
  "api_keys": [
    {
      "id": "key_abcdef123456",
      "name": "Production Key",
      "created_at": "2024-01-01T00:00:00Z",
      "last_used": "2024-01-15T09:30:00Z",
      "permissions": ["generate_apk", "download_source"]
    }
  ]
}
```

### Update User Preferences

Update user preferences and default settings.

```http
PUT /api/v1/user/preferences
```

#### Request Body

```json
{
  "default_framework": "flutter",
  "default_ui_style": "minimalist",
  "include_analytics": true,
  "notification_email": false,
  "webhook_url": "https://myapp.com/webhooks/singularity"
}
```

## Analytics and Insights

### Get Generation Analytics

Retrieve analytics for your APK generations.

```http
GET /api/v1/analytics/generations
```

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `start_date` | string | Start date (ISO 8601) |
| `end_date` | string | End date (ISO 8601) |
| `group_by` | enum | Group by: `day`, `week`, `month` |

#### Response

```json
{
  "summary": {
    "total_generations": 45,
    "successful_builds": 42,
    "success_rate": 0.93,
    "average_build_time": 156.7,
    "most_popular_framework": "react_native",
    "most_popular_category": "utility"
  },
  "timeline": [
    {
      "date": "2024-01-15",
      "generations": 5,
      "successful": 5,
      "average_build_time": 142.3
    }
  ],
  "frameworks": {
    "react_native": 28,
    "flutter": 12,
    "kivy": 3,
    "cordova": 2
  },
  "categories": {
    "utility": 15,
    "productivity": 12,
    "entertainment": 8,
    "business": 6,
    "education": 4
  }
}
```

## Webhooks

### Configure Webhooks

Set up webhooks to receive real-time notifications about APK generation progress.

```http
POST /api/v1/webhooks
```

#### Request Body

```json
{
  "url": "https://myapp.com/webhooks/singularity",
  "events": [
    "generation.started",
    "generation.completed", 
    "generation.failed",
    "generation.progress"
  ],
  "secret": "webhook_secret_key"
}
```

### Webhook Events

#### Generation Started

```json
{
  "event": "generation.started",
  "generation_id": "gen_1234567890abcdef",
  "timestamp": "2024-01-15T10:25:00Z",
  "data": {
    "app_name": "Weather Forecast Pro",
    "framework": "react_native",
    "estimated_completion": "2024-01-15T10:28:00Z"
  }
}
```

#### Generation Progress

```json
{
  "event": "generation.progress",
  "generation_id": "gen_1234567890abcdef", 
  "timestamp": "2024-01-15T10:26:30Z",
  "data": {
    "progress": 45,
    "current_stage": "generating_source_code",
    "message": "Generating weather components"
  }
}
```

#### Generation Completed

```json
{
  "event": "generation.completed",
  "generation_id": "gen_1234567890abcdef",
  "timestamp": "2024-01-15T10:28:15Z",
  "data": {
    "apk_size": 15728640,
    "build_time": 195.3,
    "download_url": "https://api.singularity.dev/api/v1/generate-apk/gen_1234567890abcdef/download"
  }
}
```

## Error Handling

### Error Response Format

All errors follow a consistent format:

```json
{
  "success": false,
  "error": {
    "code": "INVALID_PROMPT",
    "message": "The provided prompt is too vague to generate a meaningful app specification",
    "details": {
      "prompt_length": 5,
      "minimum_length": 10,
      "suggestions": [
        "Be more specific about app functionality",
        "Include target audience information",
        "Specify desired features"
      ]
    },
    "request_id": "req_1234567890abcdef"
  }
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_API_KEY` | 401 | API key is missing or invalid |
| `RATE_LIMIT_EXCEEDED` | 429 | Rate limit exceeded for current plan |
| `INVALID_PROMPT` | 400 | Prompt is too vague or invalid |
| `UNSUPPORTED_FRAMEWORK` | 400 | Requested framework is not supported |
| `GENERATION_FAILED` | 500 | APK generation failed due to internal error |
| `BUILD_TIMEOUT` | 408 | Build process exceeded maximum time limit |
| `INSUFFICIENT_CREDITS` | 402 | Account has insufficient credits |

## SDKs and Libraries

### Official SDKs

- **JavaScript/Node.js**: `npm install @singularity/sdk`
- **Python**: `pip install singularity-sdk`
- **Java**: Available via Maven Central
- **Go**: `go get github.com/singularity/go-sdk`

### JavaScript SDK Example

```javascript
import { SingularityClient } from '@singularity/sdk';

const client = new SingularityClient({
  apiKey: 'your_api_key_here',
  environment: 'production'
});

// Generate APK from text
const generation = await client.generateAPK({
  prompt: 'Create a fitness tracking app with workout plans',
  preferences: {
    framework: 'react_native',
    ui_style: 'modern'
  }
});

// Monitor progress
client.onProgress(generation.id, (progress) => {
  console.log(`Progress: ${progress.percentage}%`);
});

// Download when complete
const apkBuffer = await client.downloadAPK(generation.id);
```

### Python SDK Example

```python
from singularity_sdk import SingularityClient

client = SingularityClient(api_key='your_api_key_here')

# Generate APK
generation = client.generate_apk(
    prompt='Create a recipe sharing app with photo uploads',
    preferences={
        'framework': 'flutter',
        'ui_style': 'colorful'
    }
)

# Wait for completion
result = client.wait_for_completion(generation.id, timeout=300)

# Download APK
with open('recipe_app.apk', 'wb') as f:
    f.write(client.download_apk(generation.id))
```

## Best Practices

### Prompt Engineering

1. **Be Specific**: Include detailed functionality requirements
2. **Mention Target Audience**: Specify who will use the app
3. **Include UI Preferences**: Describe desired look and feel
4. **List Key Features**: Enumerate important capabilities
5. **Specify Integrations**: Mention required external services

#### Good Prompt Example

```
Create a fitness tracking app for runners that includes:
- GPS route tracking with maps
- Workout history and statistics
- Social sharing of achievements
- Integration with health apps
- Modern, motivational UI design
- Push notifications for workout reminders
Target audience: Recreational runners aged 25-45
```

#### Poor Prompt Example

```
Make an app
```

### Performance Optimization

1. **Choose Appropriate Framework**: React Native for cross-platform, Flutter for performance
2. **Optimize Build Settings**: Use release builds for production
3. **Monitor Generation Time**: Complex apps take longer to build
4. **Use Templates**: Start with templates for faster generation
5. **Cache API Keys**: Store frequently used API keys in preferences

### Security Considerations

1. **Protect API Keys**: Never expose API keys in client-side code
2. **Use HTTPS**: Always use secure connections
3. **Validate Webhooks**: Verify webhook signatures
4. **Rotate Keys**: Regularly rotate API keys
5. **Monitor Usage**: Watch for unusual API usage patterns

## Support and Resources

- **Documentation**: https://docs.singularity.dev
- **Community Forum**: https://community.singularity.dev
- **Status Page**: https://status.singularity.dev
- **Support Email**: support@singularity.dev
- **GitHub**: https://github.com/singularity-dev

## Changelog

### v1.2.0 (2024-01-15)
- Added Flutter framework support
- Improved AI prompt analysis accuracy
- Added template marketplace
- Enhanced error messages with suggestions

### v1.1.0 (2024-01-01)
- Added webhook support
- Improved build performance by 40%
- Added source code download option
- Enhanced analytics dashboard

### v1.0.0 (2023-12-01)
- Initial public release
- React Native and Cordova support
- Basic APK generation from text prompts
- User authentication and rate limiting
