# RNA Lab Navigator - Data Directory

This directory contains sample documents for demonstration and testing purposes.

## 📁 Directory Structure

```
data/
└── sample_docs/          # Demo documents (included in repo)
    ├── papers/          # Research papers (18 PDFs)
    ├── theses/          # Sample thesis
    ├── protocols/       # Lab protocols (9 PDFs)
    ├── inventory/       # Reagent lists (CSV)
    └── troubleshooting/ # Common issues guide
```

## 📄 Sample Documents

### Papers (`sample_docs/papers/`)
Contains 18 research papers covering:
- CRISPR-Cas9 technologies
- RNA extraction methods
- Gene editing tools
- Disease research
- AI applications in biology

### Protocols (`sample_docs/protocols/`)
Essential lab protocols including:
- RNA extraction (TRIzol)
- RT-PCR procedures
- Western blot protocols
- sgRNA design guides
- Protein purification

### Theses (`sample_docs/theses/`)
Sample PhD thesis for testing document processing.

### Inventory (`sample_docs/inventory/`)
Sample reagent inventory in CSV format.

## 🔐 Privacy Note

The `sample_docs/` directory contains only public documents or dummy data for demonstration. Actual lab documents (theses, internal protocols) should be stored securely and not committed to version control.

## 📝 Adding Documents

To add documents to the system:

1. **Via Web Interface**: Use the document upload feature
2. **Via Script**: Use `python scripts/ingest_sample_docs.py`
3. **Via API**: POST to `/api/ingestion/upload/`

## 🚫 What NOT to Store Here

- Private lab data
- Unpublished research
- Personal information
- Large datasets (>100MB)
- Proprietary protocols

## 💾 Production Data Storage

In production, documents are stored in:
- **Metadata**: PostgreSQL database
- **Vectors**: Weaviate vector database
- **Files**: Cloud storage (S3/GCS)

## 🔄 Sample Data Reset

To reset to sample data only:
```bash
./scripts/reload_sample_data.sh
```

**Warning**: This will delete all existing vectors!