# OpenAlex-Types (v0.1.1-dev0)

## Overview

OpenAlex-Types is a Python package designed to provide type definitions for interacting with the OpenAlex API, Snapshot Data, and OpenAlex objects in various databases. The package simplifies working with OpenAlex data by offering clear and concise type annotations, making it easier to manage and manipulate the data effectively. It is implemented using Pydantic, which ensures data validation and parsing, providing a robust and reliable way to handle OpenAlex data.

## Usage

Here is a basic example of how to use OpenAlex-Types in your project:

```python
import json
import gzip
from openalex_types import Work, Author

# Open and read the .gz file from snapshot
with gzip.open('snapshot_data.gz', 'rt', encoding='utf-8') as f:
    data = json.load(f) # example

# Initialize Work and Author objects
work_data = data['work']
author_data = data['author']

work = Work(**work_data)
author = Author(**author_data)

print(work)
print(author)
```
