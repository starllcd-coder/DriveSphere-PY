import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';

class AppErrorState extends StatelessWidget {
  final String title;
  final String subtitle;
  final VoidCallback onRetry;
  final bool isRetrying;
  final String? retryLabel;

  const AppErrorState({
    super.key,
    required this.title,
    required this.subtitle,
    required this.onRetry,
    this.isRetrying = false,
    this.retryLabel,
  });

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.error_outline_rounded,
            color: Colors.red[400],
            size: 50,
          ),
          const SizedBox(height: 16),
          Text(
            title,
            style: const TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.w700,
              color: Color(0xFF162E60),
            ),
          ),
          const SizedBox(height: 8),
          Text(
            subtitle,
            style: const TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.w500,
              color: Color(0xFF6B7280),
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 16),
          ElevatedButton(
            onPressed: isRetrying ? null : onRetry,
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF234E8C),
              foregroundColor: Colors.white,
              elevation: 0,
              padding: const EdgeInsets.symmetric(
                horizontal: 22,
                vertical: 12,
              ),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(14),
              ),
            ),
            child: isRetrying
                ? const SizedBox(
                    height: 18,
                    width: 18,
                    child: CircularProgressIndicator(
                      strokeWidth: 2.2,
                      color: Colors.white,
                    ),
                  )
                : Text(
                    retryLabel ?? 'common.try_again'.tr(),
                    style: const TextStyle(
                      fontWeight: FontWeight.w600,
                    ),
                  ),
          ),
        ],
      ),
    );
  }
}
