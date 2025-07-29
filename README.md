# Campaign Manager

Trying out AI (Vibe Coding) to build a scalable email campaign management system with FastAPI, Celery, PostgreSQL, and Redis. Features asynchronous recipient processing, group management, and extensible notification system.

## 🚀 Features

- **Asynchronous Campaign Processing**: Create campaigns instantly, process recipients in background
- **Recipient Management**: Store and organize recipients with groups
- **Smart Deduplication**: Automatically handle existing vs new recipients
- **Opt-out Compliance**: Built-in opt-out/opt-in functionality for GDPR compliance
- **Extensible Notifications**: Plugin-based notification system (Email, SMS, etc.)
- **Scalable Architecture**: Microservices-ready with Docker
- **Database-Driven**: PostgreSQL with SQLAlchemy ORM
- **Background Tasks**: Celery with Redis for reliable task processing
- **API-First**: RESTful API with FastAPI and automatic documentation
- **Comprehensive Logging**: Structured logging throughout the application

## 🏗️ Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   FastAPI   │───▶│   Celery    │───▶│ PostgreSQL  │
│   (API)     │    │  (Worker)   │    │  (Database) │
└─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │
       ▼                   ▼                   ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Redis     │    │  Notifiers  │    │   Groups    │
│ (Broker)    │    │ (Email/SMS) │    │ (Recipients)│
└─────────────┘    └─────────────┘    └─────────────┘
```

## 🛠️ Tech Stack

- **Backend**: FastAPI, Python 3.9+
- **Database**: PostgreSQL 15
- **Cache/Broker**: Redis 7
- **Task Queue**: Celery
- **ORM**: SQLAlchemy
- **Validation**: Pydantic with email validation
- **Containerization**: Docker & Docker Compose
- **Linting**: Pylint
- **Logging**: Python logging with structured format

## 📦 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.9+

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd campaign_manager
```

### 2. Set Up Environment
```bash
# Create .env file with your settings
cat > .env << EOF
# Database Configuration
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_DB=campaign_db
DATABASE_URL=postgresql://user:password@db:5432/campaign_db

# Celery Configuration
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Email Configuration (Optional)
SMTP_USER=your_smtp_username
SMTP_PASSWORD=your_smtp_password
SMTP_HOST=smtp.example.com
SMTP_PORT=587

# Application Configuration
LOG_LEVEL=INFO
EOF
```

### 3. Start Services
```bash
docker-compose up -d
```

### 4. Access the Application
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Database**: localhost:5432

## 📚 API Endpoints

### Campaigns
- `POST /campaigns/` - Create a new campaign
- `GET /campaigns/` - List all campaigns
- `POST /campaigns/send` - Send a campaign

### Groups
- `POST /groups/` - Create a group
- `GET /groups/` - List all groups
- `PATCH /groups/{group_id}` - Update a group's properties
- `PATCH /groups/{group_id}/recipients` - Add recipients to a group
- `GET /groups/{group_id}/recipients` - Get recipients in a group

### Recipients
- `POST /recipients/` - Create a recipient
- `GET /recipients/` - List all recipients
- `PATCH /recipients/{recipient_id}` - Update a recipient's properties
- `GET /recipients/active` - List only active (non-opted-out) recipients
- `POST /recipients/opt-out` - Opt out a recipient from communications
- `POST /recipients/opt-in` - Opt in a recipient to communications

## 🔧 Usage Examples

### Create a Campaign
```bash
curl -X POST "http://localhost:8000/campaigns/" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Welcome Campaign",
    "message": "Welcome to our platform!",
    "recipient_emails": ["user1@example.com", "user2@example.com"]
  }'
```

### Create a Group
```bash
curl -X POST "http://localhost:8000/groups/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "VIP Customers",
    "description": "High-value customers"
  }'
```

### Update a Group
```bash
curl -X PATCH "http://localhost:8000/groups/1" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated VIP Customers",
    "description": "Updated description"
  }'
```

### Add Recipients to a Group
```bash
curl -X PATCH "http://localhost:8000/groups/1/recipients" \
  -H "Content-Type: application/json" \
  -d '{
    "recipient_emails": ["user1@example.com", "user2@example.com"]
  }'
```

### Update a Recipient
```bash
curl -X PATCH "http://localhost:8000/recipients/1" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "group_id": 1,
    "opt_out": false
  }'
```

### Opt-out a Recipient
```bash
curl -X POST "http://localhost:8000/recipients/opt-out" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "reason": "No longer interested"
  }'
```

### Opt-in a Recipient
```bash
curl -X POST "http://localhost:8000/recipients/opt-in" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com"
  }'
```

## 🏛️ Project Structure

```
campaign_manager/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application with all endpoints
│   ├── models.py            # SQLAlchemy models (Campaign, Recipient, Group)
│   ├── schemas.py           # Pydantic schemas for validation
│   ├── database.py          # Database connection and session management
│   ├── worker.py            # Celery tasks for background processing
│   ├── utils.py             # Utility functions
│   ├── services/
│   │   ├── __init__.py
│   │   └── recipient_service.py  # Business logic for recipients
│   └── notifications/
│       ├── __init__.py
│       ├── base.py          # Base notifier class
│       └── email.py         # Email notifier implementation
├── docker-compose.yml       # Service orchestration
├── Dockerfile              # Application container
├── requirements.txt         # Python dependencies
├── .env                    # Environment variables (create this)
├── .gitignore             # Git ignore rules
└── README.md              # This file
```

## 🔄 Asynchronous Processing

The system uses Celery for background task processing:

1. **Campaign Creation**: Instant response, recipients processed in background
2. **Recipient Processing**: Deduplication and database linking
3. **Campaign Sending**: Uses processed recipients from database

### Background Tasks
- `process_recipients_task`: Handles recipient creation and linking
- `send_campaign_task`: Sends campaigns to active recipients

## 🧪 Development

### Running Tests
```bash
# Install dependencies
pip install -r requirements.txt

# Run linting
pylint app/

# Run tests (when implemented)
pytest
```

### Adding New Notifiers
```python
# app/notifications/sms.py
from .base import Notifier

class SMSNotifier(Notifier):
    def send(self, title: str, message: str, recipients: list[str]):
        # SMS implementation
        pass
```

### Database Migrations
The application uses SQLAlchemy's `create_all()` to automatically create tables. For production, consider using Alembic for proper migrations.

## 📈 Scalability Features

- **Horizontal Scaling**: Multiple Celery workers
- **Database Optimization**: Indexed queries, efficient relationships
- **Caching**: Redis for session and task state
- **Microservices Ready**: Containerized services
- **Environment Configuration**: Environment-based settings
- **Health Checks**: Database health monitoring
- **Error Handling**: Comprehensive error handling and logging

## 🔒 Privacy & Compliance

- **GDPR Compliance**: Built-in opt-out/opt-in functionality
- **Data Protection**: Recipient data stored securely
- **Audit Trail**: All operations logged for compliance
- **Privacy Controls**: Easy recipient management

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🚀 Future Enhancements

- [ ] Webhook notifications
- [ ] Campaign templates
- [ ] Analytics dashboard
- [ ] Rate limiting
- [ ] Authentication & Authorization
- [ ] Multi-tenant support
- [ ] A/B testing
- [ ] Email templates with variables
- [ ] Database migrations with Alembic
- [ ] Unit and integration tests
- [ ] CI/CD pipeline
- [ ] Monitoring and alerting 