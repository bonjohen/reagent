# Setting Up Web Search Functionality

This application supports web search functionality using either Serper API or Tavily API. To enable web search, you need to set up at least one of these APIs.

## Option 1: Serper API (Recommended)

Serper is a Google Search API that provides clean, structured search results.

1. Go to [Serper.dev](https://serper.dev) and sign up for an account
2. Get your API key from the dashboard
3. Set the environment variable:
   ```
   # On Windows
   setx SERPER_API_KEY your-api-key-here
   
   # On macOS/Linux
   export SERPER_API_KEY=your-api-key-here
   ```

## Option 2: Tavily API

Tavily is a search API built specifically for AI applications.

1. Go to [Tavily.com](https://tavily.com) and sign up for an account
2. Get your API key from the dashboard
3. Set the environment variable:
   ```
   # On Windows
   setx TAVILY_API_KEY your-api-key-here
   
   # On macOS/Linux
   export TAVILY_API_KEY=your-api-key-here
   ```

## Using Both APIs

You can set up both APIs if you want. The application will prefer Tavily if both are available, as it's specifically designed for AI applications.

## Verifying Setup

When you run the application, it will display which search API it's using:

```
Serper API key found. Web search will use Serper.
```

or 

```
Tavily API key found. Web search will use Tavily.
```

If no search API keys are found, you'll see a warning:

```
Warning: No search API keys found. Web search functionality will be limited.
For better search results, set SERPER_API_KEY or TAVILY_API_KEY environment variables.
```

## Troubleshooting

If you're experiencing issues with web search:

1. Make sure your API key is correct and active
2. Check that you've set the environment variable correctly
3. Ensure your API subscription is active and has available credits
4. Check the application logs for any specific error messages

For more help, visit the API provider's documentation:
- Serper: https://serper.dev/docs
- Tavily: https://docs.tavily.com
