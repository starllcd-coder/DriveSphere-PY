double _toDouble(dynamic value) {
  if (value == null) return 0;
  if (value is num) return value.toDouble();
  final text = value.toString().trim().replaceAll(',', '');
  return double.tryParse(text) ?? 0;
}

String formatCurrency(
  dynamic value, {
  String code = 'OMR',
  bool withCode = false,
}) {
  final formatted = _toDouble(value).toStringAsFixed(3);
  return withCode ? '$code $formatted' : formatted;
}

