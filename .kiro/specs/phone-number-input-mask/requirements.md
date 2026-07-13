# Requirements Document

## Introduction

This feature adds an input mask to the phone number field in the order creation form (http://127.0.0.1:8000/orders/create/). The mask will format phone numbers according to Uzbekistan's phone number format, ensuring consistent data entry and storage while improving user experience.

## Glossary

- **Phone_Input**: The telephone input field in the order creation form where users enter customer phone numbers
- **Input_Mask**: A JavaScript-based formatting mechanism that constrains and formats user input in real-time
- **Display_Format**: The formatted phone number as shown to the user: `+998 -- --- -- --`
- **Storage_Format**: The phone number format saved to the database: `-- --- -- --` (without +998 prefix)
- **Format_Handler**: The JavaScript component responsible for applying and maintaining the input mask

## Requirements

### Requirement 1: Input Mask Display

**User Story:** As a user, I want to see a formatted phone number input field, so that I know the expected format while entering the number.

#### Acceptance Criteria

1. WHEN the order creation page loads, THE Phone_Input SHALL display the placeholder `+998 -- --- -- --`
2. WHEN a user focuses on THE Phone_Input, THE Phone_Input SHALL display the `+998` prefix
3. THE Phone_Input SHALL display spaces at positions 4, 7, 10, and 13 to match the pattern `+998 XX XXX XX XX`

### Requirement 2: Numeric Input Restriction

**User Story:** As a user, I want to enter only numeric digits, so that I cannot accidentally enter invalid characters.

#### Acceptance Criteria

1. WHEN a user types a non-numeric character, THE Format_Handler SHALL ignore the input
2. WHEN a user types a numeric character, THE Format_Handler SHALL accept the digit
3. THE Format_Handler SHALL allow a maximum of 9 digits after the `+998` prefix
4. WHEN a user attempts to enter more than 9 digits, THE Format_Handler SHALL ignore additional digits

### Requirement 3: Automatic Formatting During Input

**User Story:** As a user, I want phone numbers to be formatted automatically as I type, so that I can easily read the number and verify it is correct.

#### Acceptance Criteria

1. WHEN a user types the first digit, THE Format_Handler SHALL display `+998 X` where X is the entered digit
2. WHEN a user types the second digit, THE Format_Handler SHALL maintain the format `+998 XX`
3. WHEN a user types the third digit, THE Format_Handler SHALL display `+998 XX X`
4. WHEN a user types digits 4-5, THE Format_Handler SHALL maintain spacing to show `+998 XX XXX`
5. WHEN a user types digits 6-7, THE Format_Handler SHALL maintain spacing to show `+998 XX XXX XX`
6. WHEN a user types digits 8-9, THE Format_Handler SHALL maintain spacing to show `+998 XX XXX XX XX`
7. THE Format_Handler SHALL automatically insert spaces at the correct positions without user intervention

### Requirement 4: Paste Operation Handling

**User Story:** As a user, I want to paste phone numbers from other sources, so that I can quickly fill in the form without manual typing.

#### Acceptance Criteria

1. WHEN a user pastes text containing only digits (e.g., "901234567"), THE Format_Handler SHALL format it to `+998 90 123 45 67`
2. WHEN a user pastes text starting with "+998" (e.g., "+998901234567"), THE Format_Handler SHALL format it to `+998 90 123 45 67`
3. WHEN a user pastes text starting with "998" (e.g., "998901234567"), THE Format_Handler SHALL format it to `+998 90 123 45 67`
4. WHEN a user pastes text with existing spaces (e.g., "90 123 45 67"), THE Format_Handler SHALL format it to `+998 90 123 45 67`
5. WHEN a user pastes text containing non-numeric characters, THE Format_Handler SHALL extract only the digits and format them
6. WHEN pasted content exceeds 9 digits after the prefix, THE Format_Handler SHALL use only the first 9 digits

### Requirement 5: Database Storage Format

**User Story:** As a system administrator, I want phone numbers stored without the +998 prefix, so that the database schema remains consistent with existing data.

#### Acceptance Criteria

1. WHEN the form is submitted, THE Format_Handler SHALL remove the `+998` prefix from the phone number
2. WHEN the form is submitted, THE Format_Handler SHALL remove all spaces from the phone number
3. WHEN the form is submitted, THE Phone_Input SHALL submit the phone number in the format `XXXXXXXXX` (9 digits without prefix or spaces)
4. WHEN the phone number field contains fewer than 9 digits OR WHEN the phone number field is completely empty, THE Phone_Input SHALL prevent form submission

### Requirement 6: Form Validation

**User Story:** As a user, I want to receive clear feedback if my phone number is incomplete, so that I can correct it before submitting.

#### Acceptance Criteria

1. WHEN a user attempts to submit the form with fewer than 9 digits OR WHEN the phone number field is completely empty, THE Phone_Input SHALL display a validation error message
2. THE Phone_Input validation message SHALL indicate that the phone number must be complete
3. WHEN a user enters the 9th digit, THE Phone_Input SHALL immediately remove any validation error state
4. THE Phone_Input SHALL use the browser's built-in HTML5 validation pattern

### Requirement 7: Editing Existing Phone Numbers

**User Story:** As a user, I want to edit existing phone numbers in the same formatted way, so that I have a consistent experience when updating orders.

#### Acceptance Criteria

1. WHEN the order edit page loads with an existing phone number, THE Format_Handler SHALL format the stored number to display format
2. WHEN the stored format is `XXXXXXXXX`, THE Format_Handler SHALL display it as `+998 XX XXX XX XX`
3. WHEN the display format is correct, THE Format_Handler SHALL allow editing existing phone numbers with the same mask behavior as new entries
4. WHEN editing and submitting, THE Format_Handler SHALL convert the display format back to storage format

### Requirement 8: Backspace and Delete Key Handling

**User Story:** As a user, I want to use backspace and delete keys naturally, so that I can correct mistakes easily.

#### Acceptance Criteria

1. WHEN a user presses backspace, THE Format_Handler SHALL remove the last entered digit
2. WHEN a user presses backspace at a space position, THE Format_Handler SHALL skip the space and remove the previous digit
3. WHEN a user presses delete, THE Format_Handler SHALL remove the digit at the cursor position
4. THE Format_Handler SHALL maintain proper formatting after deletion operations
5. WHEN all user-entered digits are deleted, THE Phone_Input SHALL display the `+998` prefix

### Requirement 9: Cursor Position Management

**User Story:** As a user, I want the cursor to move intelligently as I type, so that I don't have to manually adjust it when spaces are inserted.

#### Acceptance Criteria

1. WHEN a space is automatically inserted, THE Format_Handler SHALL move the cursor after the space
2. WHEN a user clicks to position the cursor within the input, THE Format_Handler SHALL allow cursor positioning
3. WHEN a user types at a cursor position in the middle of the number, THE Format_Handler SHALL maintain the correct formatting
4. WHEN a user clicks at the very beginning of the input field (before the `+998` prefix), THE Format_Handler SHALL automatically move the cursor to the first valid position after the prefix

