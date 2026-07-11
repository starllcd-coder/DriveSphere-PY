import 'package:flutter/material.dart';
import 'dart:ui';

class BrandBackground extends StatelessWidget {
  final Widget child;
  final bool dim;

  const BrandBackground({
    super.key,
    required this.child,
    this.dim = true,
  });

  @override
  Widget build(BuildContext context) {
    return Stack(
      fit: StackFit.expand,
      children: [
        Image.asset(
          'assets/images/login_bg.png',
          fit: BoxFit.cover,
        ),
        BackdropFilter(
          filter: ImageFilter.blur(sigmaX: 1.2, sigmaY: 1.2),
          child: const SizedBox.expand(),
        ),
        if (dim)
          Container(
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
                colors: [
                  Color(0xCCF7F9FC),
                  Color(0xE6EFF3FA),
                ],
              ),
            ),
          ),
        child,
      ],
    );
  }
}
