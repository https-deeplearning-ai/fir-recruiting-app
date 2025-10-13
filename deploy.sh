#!/bin/bash

# LinkedIn Assessor - Heroku Deployment Script
# This script helps you deploy your app to Heroku

set -e  # Exit on any error

echo "🚀 LinkedIn Assessor - Heroku Deployment"
echo "========================================"
echo ""

# Check if Heroku CLI is installed
if ! command -v heroku &> /dev/null; then
    echo "❌ Heroku CLI not found. Please install it first:"
    echo "   brew tap heroku/brew && brew install heroku"
    echo "   or visit: https://devcenter.heroku.com/articles/heroku-cli"
    exit 1
fi

# Check if logged in to Heroku
if ! heroku auth:whoami &> /dev/null; then
    echo "❌ Not logged in to Heroku. Running 'heroku login'..."
    heroku login
fi

echo "✅ Heroku CLI is installed and you're logged in"
echo ""

# Check if git repo is initialized
if [ ! -d .git ]; then
    echo "📦 Initializing git repository..."
    git init
    git add .
    git commit -m "Initial commit for Heroku deployment"
fi

# Check for Heroku remote
if git remote | grep -q heroku; then
    echo "✅ Heroku remote already exists"
    HEROKU_APP=$(heroku apps:info -r heroku | grep "=== " | awk '{print $2}')
    echo "   App name: $HEROKU_APP"
else
    echo ""
    read -p "📝 Enter your Heroku app name (or press Enter for auto-generated name): " APP_NAME
    
    if [ -z "$APP_NAME" ]; then
        echo "🎲 Creating Heroku app with auto-generated name..."
        heroku create
    else
        echo "🎲 Creating Heroku app: $APP_NAME..."
        heroku create "$APP_NAME"
    fi
fi

echo ""
echo "🔧 Setting up environment variables..."
echo "   (If they're already set, they will be updated)"
echo ""

# Check if environment variables are set
ENV_MISSING=false

if ! heroku config:get ANTHROPIC_API_KEY -r heroku &> /dev/null || [ -z "$(heroku config:get ANTHROPIC_API_KEY -r heroku)" ]; then
    read -p "🔑 Enter your ANTHROPIC_API_KEY: " ANTHROPIC_KEY
    heroku config:set ANTHROPIC_API_KEY="$ANTHROPIC_KEY"
    ENV_MISSING=true
fi

if ! heroku config:get CORESIGNAL_API_KEY -r heroku &> /dev/null || [ -z "$(heroku config:get CORESIGNAL_API_KEY -r heroku)" ]; then
    read -p "🔑 Enter your CORESIGNAL_API_KEY: " CORESIGNAL_KEY
    heroku config:set CORESIGNAL_API_KEY="$CORESIGNAL_KEY"
    ENV_MISSING=true
fi

if ! heroku config:get SUPABASE_URL -r heroku &> /dev/null || [ -z "$(heroku config:get SUPABASE_URL -r heroku)" ]; then
    read -p "🔑 Enter your SUPABASE_URL: " SUPABASE_URL_VALUE
    heroku config:set SUPABASE_URL="$SUPABASE_URL_VALUE"
    ENV_MISSING=true
fi

if ! heroku config:get SUPABASE_KEY -r heroku &> /dev/null || [ -z "$(heroku config:get SUPABASE_KEY -r heroku)" ]; then
    read -p "🔑 Enter your SUPABASE_KEY: " SUPABASE_KEY_VALUE
    heroku config:set SUPABASE_KEY="$SUPABASE_KEY_VALUE"
    ENV_MISSING=true
fi

if [ "$ENV_MISSING" = false ]; then
    echo "✅ All environment variables are already set"
fi

echo ""
echo "📦 Checking if there are uncommitted changes..."
if ! git diff-index --quiet HEAD --; then
    echo "   Committing changes..."
    git add .
    git commit -m "Update for Heroku deployment"
fi

echo ""
echo "🚀 Deploying to Heroku..."
git push heroku main 2>&1 || git push heroku master 2>&1

echo ""
echo "⚙️  Scaling web dyno..."
heroku ps:scale web=1

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🌐 Opening your app in the browser..."
heroku open

echo ""
echo "📊 View logs with: heroku logs --tail"
echo "🔧 Update config with: heroku config:set KEY=value"
echo "ℹ️  View app info: heroku info"
echo ""
echo "Happy coding! 🎉"

