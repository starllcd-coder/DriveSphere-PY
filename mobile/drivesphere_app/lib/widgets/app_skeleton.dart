import 'package:flutter/material.dart';

class AppSkeletonBox extends StatefulWidget {
  final double height;
  final double width;
  final BorderRadius borderRadius;

  const AppSkeletonBox({
    super.key,
    required this.height,
    this.width = double.infinity,
    this.borderRadius = const BorderRadius.all(Radius.circular(12)),
  });

  @override
  State<AppSkeletonBox> createState() => _AppSkeletonBoxState();
}

class _AppSkeletonBoxState extends State<AppSkeletonBox>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 1100),
  )..repeat(reverse: true);

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) {
        final t = _controller.value;
        return Container(
          height: widget.height,
          width: widget.width,
          decoration: BoxDecoration(
            borderRadius: widget.borderRadius,
            gradient: LinearGradient(
              begin: Alignment(-1.0 + t, -0.2),
              end: Alignment(1.0 + t, 0.2),
              colors: const [
                Color(0xFFE9EEF6),
                Color(0xFFF5F8FC),
                Color(0xFFE9EEF6),
              ],
            ),
          ),
        );
      },
    );
  }
}

class AppSkeletonList extends StatelessWidget {
  final int count;
  final EdgeInsetsGeometry padding;
  final double itemHeight;

  const AppSkeletonList({
    super.key,
    this.count = 5,
    this.padding = const EdgeInsets.fromLTRB(16, 8, 16, 24),
    this.itemHeight = 200,
  });

  @override
  Widget build(BuildContext context) {
    return ListView.separated(
      padding: padding,
      itemCount: count,
      separatorBuilder: (_, __) => const SizedBox(height: 14),
      itemBuilder: (context, index) {
        return AppSkeletonBox(
          height: itemHeight,
          borderRadius: BorderRadius.circular(22),
        );
      },
    );
  }
}
