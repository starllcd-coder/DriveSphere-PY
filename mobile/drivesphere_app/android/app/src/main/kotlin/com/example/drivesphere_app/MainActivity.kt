package com.example.drivesphere_app

import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

class MainActivity : FlutterActivity() {
	private val channel = "drivesphere/hyperpay"

	override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
		super.configureFlutterEngine(flutterEngine)
		MethodChannel(flutterEngine.dartExecutor.binaryMessenger, channel)
			.setMethodCallHandler { call, result ->
				if (call.method == "startPayment") {
					val checkoutId = call.argument<String>("checkoutId") ?: ""
					if (checkoutId.startsWith("TEST_")) {
						result.success(
							mapOf(
								"status" to "mock_success",
								"transactionId" to checkoutId
							)
						)
					} else {
						result.success(
							mapOf(
								"status" to "not_configured",
								"message" to "HyperPay SDK not configured"
							)
						)
					}
				} else {
					result.notImplemented()
				}
			}
	}
}
