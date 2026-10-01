# AAKAR Frontend V2 API Contracts

## Overview
This document defines the schemas and validation requirements for the new Project management endpoints to be implemented in Phase 2.

## 1. Project Creation
**Endpoint:** POST /api/projects
**Request Payload:**
`json
{
  "name": "Hong Kong Operations",
  "description": "Airport and terminal surveys.",
  "location": "HKG"
}
`
**Validation:**
- 
ame: Required. String (1-160 chars). Cannot be empty.
- description: Optional. String (max 2000 chars).
- location: Optional. String (max 255 chars).
**Response (201 Created):**
`json
{
  "id": "uuid-string",
  "name": "Hong Kong Operations",
  "created_at": 1727390000.0,
  "updated_at": 1727390000.0
}
`

## 2. Project Listing
**Endpoint:** GET /api/projects
**Response (200 OK):**
`json
[
  {
    "id": "default-legacy-project",
    "name": "Legacy Missions",
    "mission_count": 3
  }
]
`

## 3. Mission Creation (Backward Compatible)
**Endpoint:** POST /api/jobs
**Form Data Payload:**
- ideo: File
- gps: File (optional)
- profile: String (e.g., 'quality')
- project_id: String (optional). **If omitted, defaults to 'default-legacy-project' to preserve compatibility with existing external clients.**

## 4. Deletion and Archive Policies
- **Project Deletion (DELETE /api/projects/{pid}):** 
  - Soft-deletes the project (rchived_at = time.time()).
  - Cascades soft-delete to all child missions.
  - **Does NOT** physically delete the data/{jobId} directories to prevent irrecoverable data loss.
- **Mission Deletion (DELETE /api/jobs/{jid}):**
  - Removes the SQLite record.
  - Leaves physical directories intact, but renames the folder from data/{jobId} to data/deleted_{jobId} for retention/manual cleanup.
