# Multi-Base Arithmetic Tutorial

This example provides an interactive interface for learning multi-base arithmetic operations, specifically addition in different number bases (binary, ternary, quaternary, etc.).

## Features

- **Base Selection**: Students can specify which base they want to work in (2-9)
- **Multi-line Addition**: Visual layout similar to traditional pencil-and-paper arithmetic
- **Carry Operations**: Support for carry digits when sums exceed the base
- **Input Validation**: Ensures students use only valid digits for the selected base
- **Interactive Learning**: CTAT-enabled components provide immediate feedback

## Interface Components

### Input Fields
- **Base Input**: Single field where students specify the number base (2-9)
- **First Number (A)**: 4-digit input fields for the first addend (green border)
- **Second Number (B)**: 4-digit input fields for the second addend (red border)
- **Carry Fields**: Small fields above each column for carry digits (gray border)
- **Result Fields**: 5-digit output fields for the sum (purple border)

### Visual Layout
```
Base: [5]    
      [carry digits]
      [  A4 A3 A2 A1  ]  (First number)
    + [  B4 B3 B2 B1  ]  (Second number)
      _______________
      [R5 R4 R3 R2 R1] (base)  (Result)
```

## Usage

1. **Set the Base**: Enter a number between 2-9 in the base field
2. **Enter First Number**: Fill in the digits of the first number (right to left)
3. **Enter Second Number**: Fill in the digits of the second number (right to left)
4. **Handle Carries**: When column sums exceed (base-1), enter carry digits
5. **Calculate Result**: Enter the final sum in the result fields

## Example Problems

The configuration includes several example problems:
- `23(5)+14(5)` - Base 5 addition
- `102(3)+21(3)` - Base 3 addition  
- `101(2)+110(2)` - Binary addition
- `67(8)+54(8)` - Octal addition

## Educational Goals

Students will learn:
- Valid digits for different number bases
- Place value concepts in various bases
- Addition algorithms that work across bases
- When and how to perform carry operations
- Relationship between base and maximum digit values

## File Structure

```
MultiBaseArithmetic/
├── HTML/
│   ├── MultiBaseArithmetic.html      # Main interface
│   └── Assets/
│       └── MultiBaseArithmetic-styles.css  # Styling
├── CTAT/                             # CTAT library files
├── completeness_ground_truth.json    # Learning objectives
└── README.md                         # This file
```

## Configuration

The example is configured through `author_multibase.json` which specifies:
- Agent learning parameters
- Required practice problems  
- Skills to be assessed
- Interface location

## Integration

To use this example:
1. Ensure all CTAT dependencies are available
2. Place the MultiBaseArithmetic folder in the examples directory
3. Reference `author_multibase.json` in your training configuration
4. The agent will automatically load the HTML interface and begin tracking student interactions
