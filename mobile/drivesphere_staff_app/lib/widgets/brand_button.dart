import 'package:flutter/material.dart';
import '../core/theme/app_theme.dart';

class BrandButton extends StatelessWidget {
  final String label;
  final VoidCallback? onPressed;
  final bool loading;

  const BrandButton({
    super.key,
    required this.label,
    required this.onPressed,
    this.loading = false,
  });

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(14),
        gradient: const LinearGradient(
          colors: [AppColors.primary, AppColors.accent],
        ),
        border: Border.all(color: const Color(0x66C39A43)),
        boxShadow: const [
          BoxShadow(
            color: Color(0x2A1A3E70),
            blurRadius: 12,
            offset: Offset(0, 5),
          ),
        ],
      ),
      child: SizedBox(
        width: double.infinity,
        height: 50,
        child: Material(
          color: Colors.transparent,
          child: InkWell(
            borderRadius: BorderRadius.circular(14),
            onTap: loading ? null : onPressed,
            child: Center(
              child: loading
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(
                        strokeWidth: 2.2,
                        color: Colors.white,
                      ),
                    )
                  : Text(
                      label,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 18,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
            ),
          ),
        ),
      ),
    );
  }
}
