# Smart Notebook - Backend API

Backend service for the Smart Notebook application.

## Structure

```
backend/
├── migrations/      # Database migration scripts
├── utils/          # Database utilities and diagnostics
├── scripts/        # Setup and deployment scripts
└── src/            # Backend source code (add your API code here)
```

## Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Set up Supabase connection
3. Run migrations in `migrations/` folder
4. Start the backend server

## Utilities

- **diagnose_supabase.py**: Check database connection and structure
- **verify_supabase_setup.py**: Verify database setup
- **check_sync_status.py**: Monitor sync status
