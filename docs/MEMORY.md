# Memory Management Feature

This document provides information about the Memory Management feature added to the Agent CLI Orchestrator.

## Overview

The Memory Management system allows users to store, retrieve, update, and delete personal memories through a RESTful API. Each memory can include content, tags, and custom metadata, making it easy to organize and search through memories.

## Features

- ✅ **Create Memories**: Store new memories with content, tags, and metadata
- ✅ **List Memories**: Retrieve all memories for a user with optional pagination
- ✅ **Get Last Memory**: Quickly access the most recently created memory
- ✅ **Get Memory by ID**: Retrieve a specific memory using its unique identifier
- ✅ **Update Memories**: Modify existing memories (content, tags, or metadata)
- ✅ **Delete Memories**: Remove memories that are no longer needed
- ✅ **Search Memories**: Find memories by searching their content
- ✅ **User Isolation**: Memories are completely isolated per user
- ✅ **Persistent Storage**: All memories are stored in YAML files

## Quick Start

### Creating a Memory

```bash
curl -X POST "http://localhost:8000/memories/" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "your_user_id",
    "content": "I learned about FastAPI today",
    "tags": ["learning", "python", "fastapi"],
    "metadata": {"difficulty": "intermediate"}
  }'
```

### Getting All Memories

```bash
curl "http://localhost:8000/memories/?user_id=your_user_id"
```

### Getting the Last Memory

```bash
curl "http://localhost:8000/memories/last?user_id=your_user_id"
```

### Searching Memories

```bash
curl "http://localhost:8000/memories/search/?user_id=your_user_id&query=FastAPI"
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/memories/` | Create a new memory |
| GET | `/memories/` | Get all memories for a user |
| GET | `/memories/last` | Get the most recent memory |
| GET | `/memories/{memory_id}` | Get a specific memory by ID |
| PUT | `/memories/{memory_id}` | Update a memory |
| DELETE | `/memories/{memory_id}` | Delete a memory |
| GET | `/memories/search/` | Search memories by content |

For detailed API documentation, see [API.md](../API.md#memory-management).

## Data Structure

Each memory has the following structure:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user123",
  "content": "Memory content goes here",
  "created_at": "2026-01-27T10:22:03.748358+00:00",
  "updated_at": "2026-01-27T10:22:03.748361+00:00",
  "tags": ["tag1", "tag2"],
  "metadata": {
    "custom_field": "custom_value"
  }
}
```

## Storage

Memories are stored in YAML files in the `./data/memories/` directory. Each user has their own file:

```
./data/memories/
  ├── user_alice_memories.yaml
  ├── user_bob_memories.yaml
  └── user_charlie_memories.yaml
```

## Python Usage Example

```python
import requests

BASE_URL = "http://localhost:8000"
USER_ID = "my_user_id"

# Create a memory
response = requests.post(
    f"{BASE_URL}/memories/",
    json={
        "user_id": USER_ID,
        "content": "My first memory",
        "tags": ["important"],
        "metadata": {"category": "personal"}
    }
)
memory = response.json()["memory"]

# Get all memories
response = requests.get(f"{BASE_URL}/memories/?user_id={USER_ID}")
memories = response.json()["memories"]

# Get last memory
response = requests.get(f"{BASE_URL}/memories/last?user_id={USER_ID}")
last_memory = response.json()["memory"]

# Search memories
response = requests.get(
    f"{BASE_URL}/memories/search/?user_id={USER_ID}&query=first"
)
results = response.json()["memories"]
```

## Use Cases

1. **Learning Journal**: Track what you learn each day
2. **Project Notes**: Remember key decisions and insights from projects
3. **Personal Diary**: Store personal thoughts and experiences
4. **Code Snippets**: Save useful code patterns with explanations
5. **Meeting Notes**: Keep track of important discussions
6. **Ideas**: Capture creative ideas and inspirations

## Configuration

The memory storage location can be configured in `main.py`:

```python
memory_service = MemoryService(storage_dir="./data/memories")
```

## Testing

Run the memory service tests:

```bash
pytest tests/memory/test_memory_service.py -v
```

All tests are passing:
- ✅ Create memory
- ✅ Get memories
- ✅ Get memories with limit
- ✅ Get last memory
- ✅ Get memory by ID
- ✅ Update memory
- ✅ Delete memory
- ✅ Search memories
- ✅ Multiple users isolation

## Security

- ✅ CodeQL security scan passed (0 alerts)
- ✅ No security vulnerabilities detected
- ✅ User data is isolated per user
- ✅ Input validation using Pydantic models

## Implementation Details

### Components

1. **Memory Service** (`src/memory/service.py`)
   - Core business logic for CRUD operations
   - Uses YAML backend for persistent storage
   - Handles memory sorting and searching

2. **Memory Models** (`src/memory/models.py`)
   - Pydantic v2 models for data validation
   - Request/response models for API
   - Proper datetime handling with timezone awareness

3. **Memory Routes** (`src/api/routes/memory.py`)
   - RESTful API endpoints
   - Error handling and validation
   - Consistent response format

### Design Decisions

- **YAML Storage**: Chosen for human-readability and compatibility with existing storage patterns
- **Per-User Files**: Simplifies querying and improves performance
- **UUID Identifiers**: Ensures global uniqueness of memory IDs
- **Timezone-Aware Datetimes**: Prevents timezone-related bugs
- **Tags and Metadata**: Flexible organization system

## Future Enhancements

Potential improvements for future versions:

- [ ] Full-text search with indexing
- [ ] Memory categories/folders
- [ ] Sharing memories between users
- [ ] Export memories to various formats (JSON, Markdown, PDF)
- [ ] Memory templates
- [ ] Automatic tagging using AI
- [ ] Memory reminders/notifications
- [ ] Memory analytics and insights

## Troubleshooting

**Q: Where are my memories stored?**
A: Memories are stored in YAML files in the `./data/memories/` directory.

**Q: Can other users see my memories?**
A: No, memories are completely isolated per user. Each user can only access their own memories.

**Q: What happens if I delete a memory?**
A: Once deleted, a memory cannot be recovered unless you have a backup of the YAML file.

**Q: Can I backup my memories?**
A: Yes, simply copy the `./data/memories/` directory to create a backup.

**Q: Is there a limit to how many memories I can store?**
A: There's no hard limit, but performance may decrease with very large numbers of memories (10,000+).

## Support

For issues or questions about the Memory Management feature, please:
1. Check the API documentation in [API.md](../API.md#memory-management)
2. Run the test suite to verify functionality
3. Check the server logs for error messages
