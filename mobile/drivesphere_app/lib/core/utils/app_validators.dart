class AppValidators {
  static String? requiredField(String value, String label) {
    if (value.trim().isEmpty) {
      return '$label is required.';
    }
    return null;
  }

  static String? positiveNumber(String value, String label) {
    if (value.trim().isEmpty) {
      return '$label is required.';
    }

    final number = double.tryParse(value.trim());
    if (number == null || number <= 0) {
      return 'Enter a valid $label.';
    }

    return null;
  }

  static String? integerId(String value, String label) {
    if (value.trim().isEmpty) {
      return '$label is required.';
    }

    final parsed = int.tryParse(value.trim());
    if (parsed == null || parsed <= 0) {
      return 'Enter a valid $label.';
    }

    return null;
  }
}