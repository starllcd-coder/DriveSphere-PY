import 'package:drivesphere_app/core/theme/app_theme.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('app theme can be created', () {
    final theme = AppTheme.lightTheme;
    expect(theme, isNotNull);
  });
}
