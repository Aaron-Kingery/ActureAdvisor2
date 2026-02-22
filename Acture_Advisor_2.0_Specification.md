# Acture Advisor 2.0 — Technical Specification

**Version:** 1.0  
**Date:** January 6, 2026  
**Status:** Draft  
**Client:** Acture Solutions  

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Overview](#2-system-overview)
3. [Functional Requirements](#3-functional-requirements)
4. [Non-Functional Requirements](#4-non-functional-requirements)
5. [Technical Specifications](#5-technical-specifications)
6. [Data Model](#6-data-model)
7. [API Endpoints](#7-api-endpoints)
8. [User Interface](#8-user-interface)
9. [Deployment](#9-deployment)
10. [Acceptance Criteria](#10-acceptance-criteria)
11. [Appendix](#11-appendix)

---

## 1. Executive Summary

Acture Advisor 2.0 is an internal knowledge assistant application designed to provide Acture Solutions staff with instant, accurate answers sourced exclusively from approved internal documentation. The system leverages Retrieval-Augmented Generation (RAG) technology to search and synthesize information from SharePoint or Google Drive document repositories.

Key capabilities include AI-powered question answering with source citations, feedback collection for continuous improvement, administrative review of failed queries, and an integrated KB article authoring tool that transforms unstructured content into professionally formatted knowledge base articles.

### 1.1 Project Goals

- Reduce time spent searching for internal information
- Ensure answers are grounded in approved documentation only
- Maintain security with no third-party data exposure
- Enable continuous improvement through feedback mechanisms
- Streamline KB article creation with AI-assisted formatting

---

## 2. System Overview

### 2.1 High-Level Architecture

The application follows a modern three-tier architecture deployed on a self-hosted Linux server:

| Tier | Components | Technology |
|------|------------|------------|
| Presentation | Web UI, Chat Interface, Admin Dashboard | React/Next.js |
| Application | API Server, RAG Pipeline, Auth Service | Python (FastAPI) |
| Data | Vector Store, Relational DB, Document Cache | PostgreSQL + pgvector |

### 2.2 Core Components

#### 2.2.1 Document Ingestion Pipeline

Responsible for:
- Synchronizing documents from the configured source (SharePoint or Google Drive)
- Extracting text content from supported file types
- Chunking documents into semantic segments
- Generating vector embeddings
- Maintaining the vector index

#### 2.2.2 RAG Query Engine

Processes user questions by:
- Converting questions to vector embeddings
- Retrieving relevant document chunks via similarity search
- Constructing prompts with retrieved context
- Generating responses via the LLM
- Extracting and formatting source citations

#### 2.2.3 KB Article Formatter

- Accepts unformatted text input from administrators
- Applies AI processing for structure, clarity, and completeness
- Formats content according to saved templates (KB or Policy)
- Provides preview before publishing to the document source

---

## 3. Functional Requirements

### 3.1 Authentication & Authorization

| ID | Requirement |
|----|-------------|
| FR-1.1 | System shall support Single Sign-On via Google OAuth 2.0 OR Microsoft Entra ID (Azure AD), configured at deployment time |
| FR-1.2 | Authentication provider selection shall be a one-time configuration that also determines the document source (Google = Google Drive, Microsoft = SharePoint) |
| FR-1.3 | System shall support two roles: User and Admin |
| FR-1.4 | Users shall be able to access chat interface and provide feedback |
| FR-1.5 | Admins shall have all User permissions plus access to review dashboard, KB formatter, and analytics |

### 3.2 Document Management

| ID | Requirement |
|----|-------------|
| FR-2.1 | System shall connect to a single configured SharePoint site OR Google Drive folder based on authentication provider |
| FR-2.2 | Supported file formats: PDF, DOCX, XLSX, Markdown (.md), Plain Text (.txt) |
| FR-2.3 | Document synchronization shall run automatically every 4 hours |
| FR-2.4 | Sync process shall add new documents, update modified documents, and remove documents deleted from source |
| FR-2.5 | System shall maintain document metadata including source URL, last modified date, and file type |

### 3.3 Question & Answer Interface

| ID | Requirement |
|----|-------------|
| FR-3.1 | Users shall be able to submit natural language questions via web chat interface |
| FR-3.2 | System shall answer questions ONLY using content from indexed internal documents |
| FR-3.3 | When unable to answer from internal documents, system shall clearly state this limitation |
| FR-3.4 | All answers shall include clickable links to source document(s) used |
| FR-3.5 | Multiple source documents may be cited when answer synthesizes information from several sources |
| FR-3.6 | Conversation history shall NOT persist between sessions |

### 3.4 Feedback System

| ID | Requirement |
|----|-------------|
| FR-4.1 | Each response shall display thumbs up and thumbs down buttons |
| FR-4.2 | System shall record all questions and answers that receive thumbs down feedback |
| FR-4.3 | System shall record all questions that could not be answered from internal documents |
| FR-4.4 | Recorded feedback items shall include: timestamp, user ID, question text, response text, feedback type, source documents (if any) |
| FR-4.5 | Thumbs up feedback shall be counted for analytics but detailed records not retained |

### 3.5 Admin Review Dashboard

| ID | Requirement |
|----|-------------|
| FR-5.1 | Admins shall access review queue via same web interface as chat |
| FR-5.2 | Dashboard shall display list of flagged items (thumbs down + unanswered) |
| FR-5.3 | Each item shall show: question, response, source docs, user, timestamp, status |
| FR-5.4 | Status workflow: New → In Review → Resolved |
| FR-5.5 | Admins shall be able to add notes to reviewed items |
| FR-5.6 | Dashboard shall display success rate metric (answered / total questions) |

### 3.6 KB Article Formatter

| ID | Requirement |
|----|-------------|
| FR-6.1 | Admin-only feature accessible from main web interface |
| FR-6.2 | Accept unformatted text via paste or text input |
| FR-6.3 | Support two templates: KB Article and Policy Document |
| FR-6.4 | AI shall format content according to selected template structure |
| FR-6.5 | AI shall make reasonable additions for completeness and clarity |
| FR-6.6 | Preview formatted article before publishing |
| FR-6.7 | Publish approved articles directly to configured document source (SharePoint/Google Drive) |

---

## 4. Non-Functional Requirements

### 4.1 Performance

| ID | Specification |
|----|---------------|
| NFR-1.1 | Query response time: < 10 seconds for 95th percentile |
| NFR-1.2 | Document sync: Process 100 documents within 30 minutes |
| NFR-1.3 | Concurrent users: Support minimum 10 simultaneous chat sessions |
| NFR-1.4 | UI responsiveness: Page load < 3 seconds |

### 4.2 Security

| ID | Specification |
|----|---------------|
| NFR-2.1 | All data shall remain on-premises; no transmission to third parties |
| NFR-2.2 | When using OpenAI API, only query context sent (not full documents) |
| NFR-2.3 | Ollama fallback ensures fully air-gapped operation capability |
| NFR-2.4 | All API endpoints require authentication |
| NFR-2.5 | HTTPS encryption for all web traffic (Nginx + Let's Encrypt) |
| NFR-2.6 | Database credentials stored in environment variables, not code |

### 4.3 Reliability

| ID | Specification |
|----|---------------|
| NFR-3.1 | LLM failover: Automatic fallback from OpenAI to Ollama on failure |
| NFR-3.2 | Document sync: Retry failed documents up to 3 times |
| NFR-3.3 | Database: Daily automated backups |
| NFR-3.4 | Application logs retained for 30 days |

---

## 5. Technical Specifications

### 5.1 Infrastructure

| Component | Specification |
|-----------|---------------|
| Operating System | Linux (Ubuntu Server 22.04 LTS recommended) |
| CPU | 24 cores |
| Memory | 32 GB RAM |
| Storage | 100 GB HDD (SSD recommended for vector operations) |
| Web Server | Nginx (reverse proxy, SSL termination) |
| SSL | Let's Encrypt (final deployment phase) |

### 5.2 Software Stack

| Layer | Technology | Version/Notes |
|-------|------------|---------------|
| Frontend | React or Next.js | Latest LTS |
| Backend API | Python FastAPI | 0.100+ |
| Database | PostgreSQL + pgvector | PostgreSQL 15+, pgvector 0.5+ |
| Vector Store | pgvector extension | Integrated with PostgreSQL |
| RAG Framework | LangChain or LlamaIndex | Latest stable |
| Containerization | Docker + Docker Compose | Optional but recommended |

### 5.3 LLM Configuration

#### 5.3.1 Primary: OpenAI API

| Setting | Value |
|---------|-------|
| Model | gpt-4o-mini (cost-effective) or gpt-4o (higher quality) |
| Temperature | 0.1 (low for factual accuracy) |
| Max Tokens | 1024 |
| Timeout | 30 seconds |

#### 5.3.2 Fallback: Ollama (Local)

| Setting | Value |
|---------|-------|
| Model | llama3.2:3b (recommended for 32GB RAM) |
| Alternative | phi3:mini (lighter, Microsoft-backed) |
| Context Window | 4096 tokens |
| Trigger | Automatic on OpenAI API failure or timeout |

### 5.4 Embedding Model

**Recommended:** nomic-embed-text via Ollama

| Property | Value |
|----------|-------|
| Model | nomic-embed-text |
| Dimensions | 768 |
| Provider | Ollama (local) |
| Rationale | High quality, runs locally, no API costs, good performance on retrieval benchmarks |
| Alternative | OpenAI text-embedding-3-small (if API preferred) |

### 5.5 Document Processing

| File Type | Processing Method |
|-----------|-------------------|
| PDF | PyMuPDF (fitz) for text extraction |
| DOCX | python-docx for text and structure |
| XLSX | openpyxl with sheet-by-sheet processing |
| Markdown | Direct text ingestion with frontmatter parsing |
| Plain Text | Direct ingestion |

#### 5.5.1 Chunking Strategy

| Parameter | Value |
|-----------|-------|
| Chunk Size | 512 tokens |
| Chunk Overlap | 50 tokens |
| Splitter | RecursiveCharacterTextSplitter |
| Metadata Preserved | Source URL, document title, page/section number |

---

## 6. Data Model

### 6.1 Core Tables

#### users

| Column | Type / Description |
|--------|-------------------|
| id | UUID, Primary Key |
| email | VARCHAR(255), Unique, from SSO |
| display_name | VARCHAR(255) |
| role | ENUM ('user', 'admin') |
| created_at | TIMESTAMP |
| last_login | TIMESTAMP |

#### documents

| Column | Type / Description |
|--------|-------------------|
| id | UUID, Primary Key |
| source_url | TEXT, link to original document |
| title | VARCHAR(500) |
| file_type | VARCHAR(20) |
| content_hash | VARCHAR(64), for change detection |
| last_synced | TIMESTAMP |
| created_at | TIMESTAMP |

#### document_chunks

| Column | Type / Description |
|--------|-------------------|
| id | UUID, Primary Key |
| document_id | UUID, Foreign Key → documents |
| chunk_index | INTEGER |
| content | TEXT |
| embedding | VECTOR(768), pgvector type |
| metadata | JSONB (page number, section, etc.) |

#### queries

| Column | Type / Description |
|--------|-------------------|
| id | UUID, Primary Key |
| user_id | UUID, Foreign Key → users |
| question | TEXT |
| response | TEXT |
| answered | BOOLEAN |
| source_doc_ids | UUID[], array of document IDs |
| created_at | TIMESTAMP |

#### feedback

| Column | Type / Description |
|--------|-------------------|
| id | UUID, Primary Key |
| query_id | UUID, Foreign Key → queries |
| feedback_type | ENUM ('positive', 'negative') |
| status | ENUM ('new', 'in_review', 'resolved') |
| admin_notes | TEXT |
| reviewed_by | UUID, Foreign Key → users |
| reviewed_at | TIMESTAMP |
| created_at | TIMESTAMP |

#### kb_templates

| Column | Type / Description |
|--------|-------------------|
| id | UUID, Primary Key |
| name | VARCHAR(100), e.g., 'KB Article', 'Policy' |
| template_content | TEXT, template structure/instructions |
| created_at | TIMESTAMP |
| updated_at | TIMESTAMP |

---

## 7. API Endpoints

### 7.1 Authentication

| Endpoint | Description |
|----------|-------------|
| GET /auth/login | Initiate SSO flow (redirects to Google/Entra) |
| GET /auth/callback | SSO callback handler |
| POST /auth/logout | End session |
| GET /auth/me | Get current user info |

### 7.2 Chat

| Endpoint | Description |
|----------|-------------|
| POST /api/chat | Submit question, receive answer with sources |
| POST /api/chat/{id}/feedback | Submit thumbs up/down for a response |

### 7.3 Admin

| Endpoint | Description |
|----------|-------------|
| GET /api/admin/feedback | List flagged items (negative + unanswered) |
| PATCH /api/admin/feedback/{id} | Update status, add notes |
| GET /api/admin/stats | Get success rate and query counts |
| GET /api/admin/templates | List KB templates |
| POST /api/admin/kb/format | Format raw text using template |
| POST /api/admin/kb/preview | Generate preview of formatted article |
| POST /api/admin/kb/publish | Publish to document source |

### 7.4 System

| Endpoint | Description |
|----------|-------------|
| POST /api/sync/trigger | Manually trigger document sync (admin only) |
| GET /api/sync/status | Get last sync status and next scheduled time |
| GET /api/health | Health check endpoint |

---

## 8. User Interface

### 8.1 Branding

| Element | Specification |
|---------|---------------|
| Logo | Acture Solutions logo (from acturesolutions.com) |
| Primary Color | #6B2D8B (Acture Purple) |
| Secondary Color | #2D2D2D (Dark Gray) |
| Accent Color | #E8D5F0 (Light Purple) |
| Font Family | Arial or system sans-serif |
| Application Name | Acture Advisor 2.0 |

### 8.2 Main Views

#### 8.2.1 Chat Interface (All Users)

- Clean, centered chat window with message input at bottom
- User messages aligned right, assistant responses aligned left
- Source links displayed below each response as clickable chips
- Thumbs up/down buttons below each response
- Clear indicator when query cannot be answered from internal docs

#### 8.2.2 Admin Dashboard

- Navigation: Chat | Review Queue | KB Formatter | Analytics
- Review Queue: Filterable table (by status, date), expandable rows
- Success rate displayed prominently on dashboard

#### 8.2.3 KB Formatter

- Left panel: Raw text input area
- Template selector dropdown (KB Article / Policy)
- Right panel: Formatted preview (live or on-demand)
- Action buttons: Format, Preview, Publish

---

## 9. Deployment

### 9.1 Deployment Phases

| Phase | Components | Notes |
|-------|------------|-------|
| Phase 1 | Backend API, PostgreSQL, Ollama | Core functionality, local LLM only |
| Phase 2 | Frontend UI, SSO Integration | User-facing interface |
| Phase 3 | OpenAI Integration, Document Sync | External API, scheduled jobs |
| Phase 4 | KB Formatter, Admin Dashboard | Admin features |
| Phase 5 | Nginx, Let's Encrypt SSL | Production hardening |

### 9.2 Configuration

All configuration via environment variables:

| Variable | Description |
|----------|-------------|
| AUTH_PROVIDER | 'google' or 'microsoft' |
| GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET | Google OAuth credentials (if Google) |
| AZURE_CLIENT_ID / AZURE_TENANT_ID / AZURE_CLIENT_SECRET | Entra credentials (if Microsoft) |
| SHAREPOINT_SITE_URL | SharePoint document library URL (if Microsoft) |
| GOOGLE_DRIVE_FOLDER_ID | Google Drive folder ID (if Google) |
| OPENAI_API_KEY | OpenAI API key (optional, enables primary LLM) |
| OLLAMA_BASE_URL | Ollama server URL (default: http://localhost:11434) |
| DATABASE_URL | PostgreSQL connection string |
| SECRET_KEY | Application secret for session encryption |

### 9.3 Scheduled Jobs

| Job | Schedule |
|-----|----------|
| Document Sync | Every 4 hours (0 */4 * * *) |
| Database Backup | Daily at 2:00 AM |
| Log Rotation | Daily |

---

## 10. Acceptance Criteria

### 10.1 Authentication

- [ ] User can log in via configured SSO provider
- [ ] Unauthorized users cannot access any application features
- [ ] Admin features are not visible/accessible to regular users

### 10.2 Question Answering

- [ ] System answers questions using only indexed document content
- [ ] Each answer includes at least one source document link
- [ ] System clearly indicates when it cannot answer from available documents
- [ ] Source links open the correct document in SharePoint/Google Drive

### 10.3 Feedback & Review

- [ ] Thumbs down responses appear in admin review queue
- [ ] Unanswered queries appear in admin review queue
- [ ] Admin can update status and add notes to flagged items
- [ ] Success rate metric accurately reflects answered vs total queries

### 10.4 Document Sync

- [ ] New documents in source appear in search results after sync
- [ ] Deleted documents no longer appear in search results after sync
- [ ] Modified documents reflect updated content after sync

### 10.5 KB Formatter

- [ ] Unformatted text is transformed to match selected template structure
- [ ] Preview accurately represents final document appearance
- [ ] Published articles appear in configured document source

### 10.6 LLM Failover

- [ ] System continues to answer questions when OpenAI API is unavailable
- [ ] Failover to Ollama is automatic and transparent to users

---

## 11. Appendix

### 11.1 Glossary

| Term | Definition |
|------|------------|
| RAG | Retrieval-Augmented Generation — technique combining document retrieval with LLM generation |
| LLM | Large Language Model — AI model for natural language understanding and generation |
| SSO | Single Sign-On — authentication allowing one login for multiple systems |
| pgvector | PostgreSQL extension for vector similarity search |
| Embedding | Numerical vector representation of text for semantic search |
| Ollama | Open-source tool for running LLMs locally |
| Chunk | Segment of document text used for retrieval |

### 11.2 Document Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | January 6, 2026 | Initial specification document |

### 11.3 Open Questions / Future Considerations

- Multi-language support for documents and queries
- Integration with ticketing systems for escalation workflow
- User conversation history (currently scoped out)
- Mobile application or embedded widget deployment
- Advanced analytics and usage reporting

---

*— End of Document —*
