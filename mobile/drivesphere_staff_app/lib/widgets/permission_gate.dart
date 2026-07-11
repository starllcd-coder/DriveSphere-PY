import 'package:flutter/material.dart';

import '../services/staff_api_service.dart';

class PermissionGate extends StatefulWidget {
  final List<String> anyOf;
  final Widget child;

  const PermissionGate({
    super.key,
    required this.anyOf,
    required this.child,
  });

  @override
  State<PermissionGate> createState() => _PermissionGateState();
}

class _PermissionGateState extends State<PermissionGate> {
  final _api = StaffApiService();
  late Future<bool> _allowedFuture;

  @override
  void initState() {
    super.initState();
    _allowedFuture = _api.hasAnyPermission(widget.anyOf);
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<bool>(
      future: _allowedFuture,
      builder: (context, snapshot) {
        if (snapshot.connectionState != ConnectionState.done) {
          return const Scaffold(
            body: Center(child: CircularProgressIndicator()),
          );
        }
        final allowed = snapshot.data == true;
        if (allowed) return widget.child;
        return const Scaffold(
          body: Center(
            child: Text('You do not have permission to access this screen.'),
          ),
        );
      },
    );
  }
}

