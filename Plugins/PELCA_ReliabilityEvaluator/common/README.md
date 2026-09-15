# Common Helpers

This package contains shared utilities used by several reliability evaluators.

Keep only genuinely shared logic here. Subsystem-specific equations, constants and model assumptions should stay inside the relevant subsystem folder.

## Files

- `excel_parameters.py`: reads key/value parameter blocks from Excel sheets.

## Current Usage

The shared Excel reader is used by several subsystem evaluators to load parameter sheets with a consistent pattern. It helps keep the subsystem entry points focused on reliability calculations rather than workbook parsing details.

## Contribution Notes

Add code here only when it is reusable across at least two subsystems. Good candidates include:

- generic workbook parsing;
- unit conversion helpers;
- common result-formatting utilities;
- shared validation helpers.

Avoid adding subsystem-specific reliability equations in this package.
