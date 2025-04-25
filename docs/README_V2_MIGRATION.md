# aGENtrader v2 Migration

This repository has been reorganized to separate the v1 and v2 implementations:

## aGENtrader_v1/
Contains the original implementation with the Node.js Express API and Python backend.
This is an archived version for reference purposes.

## aGENtrader_v2/
Contains the new implementation built with AutoGen Core. This is a completely
decoupled system with its own architecture and pipeline.

## Migration Process

The separation allows for:
1. Clean development of v2 without affecting v1
2. Potential for side-by-side comparisons
3. Future complete separation into different repositories

## GitHub Organization

For GitHub, we recommend:
1. Maintaining this as the main repository for active v2 development
2. Creating a separate archived repository for v1 if needed
