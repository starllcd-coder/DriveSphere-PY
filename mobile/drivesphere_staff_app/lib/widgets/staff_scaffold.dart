import 'package:flutter/material.dart';

import 'brand_background.dart';
import 'glass_panel.dart';

class StaffScaffold extends StatelessWidget {
  final String title;
  final Widget body;
  final List<Widget>? actions;
  final bool showBackButton;

  const StaffScaffold({
    super.key,
    required this.title,
    required this.body,
    this.actions,
    this.showBackButton = true,
  });

  @override
  Widget build(BuildContext context) {
    final canPop = Navigator.of(context).canPop();
    return Scaffold(
      extendBodyBehindAppBar: true,
      appBar: AppBar(
        automaticallyImplyLeading: showBackButton && canPop,
        title: Text(title),
        titleSpacing: showBackButton && canPop ? null : 16,
        actions: actions,
      ),
      body: BrandBackground(
        child: SafeArea(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(16, 10, 16, 14),
            child: Center(
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 1120),
                child: GlassPanel(
                  padding: const EdgeInsets.all(14),
                  child: body,
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
