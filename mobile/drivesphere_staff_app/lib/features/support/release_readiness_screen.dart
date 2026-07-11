import 'package:flutter/material.dart';

import '../../widgets/staff_scaffold.dart';

class ReleaseReadinessScreen extends StatelessWidget {
  const ReleaseReadinessScreen({super.key});

  @override
  Widget build(BuildContext context) {
    const checks = [
      'Auth and role guard wired',
      'Branch scoping wired',
      'Core modules routed',
      'Maintenance list and done flow wired',
      'Employees and reports screens wired',
      'Notifications/profile screens scaffolded',
      'QA/UAT checklist pending',
      'Store/MDM release pipeline pending',
    ];

    return StaffScaffold(
      title: 'Release Readiness',
      body: ListView.separated(
        itemCount: checks.length,
        separatorBuilder: (_, __) => const SizedBox(height: 8),
        itemBuilder: (_, index) => ListTile(
          tileColor: Colors.white,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(10),
            side: const BorderSide(color: Color(0xFFD8DFEC)),
          ),
          leading: Icon(
            index <= 5 ? Icons.check_circle_outline : Icons.radio_button_unchecked,
            color: index <= 5 ? const Color(0xFF1F7A48) : const Color(0xFF9AA5B7),
          ),
          title: Text(checks[index]),
        ),
      ),
    );
  }
}

