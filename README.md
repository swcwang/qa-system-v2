# Q&A System V2

Clean, refactored version of the Q&A search tool with external configuration.

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Copy your data:**
   ```bash
   # Copy JSON files to data/input_json2/
   # Copy ChromaDB to data/chroma_db_large/
   ```

3. **Setup and test:**
   ```python
   from qanda_module import setup_system
   
   helpers, qa_chain, config = setup_system()
   # Should work if data is in place
   ```

## Configuration

Edit `config.yaml` to customize:
- Model settings (embedding model, chat model)
- Data paths
- Enhancement parameters
- Debug settings

## Project Structure

```
qanda-v2/
├── config.yaml              # Main configuration
├── qanda_module/            # Core package
│   ├── config.py           # Configuration system
│   ├── database_clean.py   # Clean data loading
│   └── retrieval_lean.py   # Simplified pipeline
├── data/                   # Data directory
├── notebooks/              # Development notebooks
└── tests/                  # Test files
```

## Migration from V1

1. Copy data files to `data/` directory
2. Copy working functions from old project to `legacy_imports.py`
3. Update import paths
4. Test with simple queries

## Development

- Use `notebooks/` for experimentation
- Configuration in `config.yaml`
- All imports from `qanda_module`
- Git tracking enabled

## Next Steps

1. Copy missing functions from old project
2. Add proper UI integration
3. Add comprehensive tests
4. Deploy with clean configuration
