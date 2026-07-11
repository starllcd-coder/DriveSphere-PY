import 'dart:typed_data';

import 'package:easy_localization/easy_localization.dart';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import '../../core/utils/app_message_helper.dart';
import '../../core/utils/app_validators.dart';
import '../../models/document_model.dart';
import '../../services/api_service.dart';
import '../../widgets/app_empty_state.dart';
import '../../widgets/app_error_state.dart';
import '../../widgets/app_loading_indicator.dart';
import '../../widgets/app_primary_button.dart';
import '../../widgets/app_snackbar.dart';

class DocumentsScreen extends StatefulWidget {
  const DocumentsScreen({super.key});

  @override
  State<DocumentsScreen> createState() => _DocumentsScreenState();
}

class _DocumentsScreenState extends State<DocumentsScreen> {
  final ApiService _apiService = ApiService();

  final TextEditingController _customerIdController =
      TextEditingController(text: '1');
  final TextEditingController _docTypeController =
      TextEditingController(text: 'LICENSE');
  final TextEditingController _expiryDateController = TextEditingController();
  final TextEditingController _notesController = TextEditingController();

  late Future<List<DocumentModel>> _documentsFuture;

  Uint8List? _selectedFileBytes;
  String? _selectedFileName;
  bool _uploading = false;
  final ImagePicker _imagePicker = ImagePicker();

  @override
  void initState() {
    super.initState();
    _documentsFuture = _loadDocuments();
  }

  Future<List<DocumentModel>> _loadDocuments() async {
    final customerId = int.tryParse(_customerIdController.text.trim()) ?? 1;
    return _apiService.fetchDocuments(customerId: customerId);
  }

  Future<void> _refreshDocuments() async {
    setState(() {
      _documentsFuture = _loadDocuments();
    });
  }

  Future<void> _pickFile() async {
    final result = await FilePicker.platform.pickFiles(
      withData: true,
      allowMultiple: false,
    );

    if (result != null && result.files.isNotEmpty) {
      final file = result.files.first;
      if (file.bytes != null) {
        setState(() {
          _selectedFileBytes = file.bytes!;
          _selectedFileName = file.name;
        });
      }
    }
  }

  Future<void> _pickFromCamera() async {
    final file = await _imagePicker.pickImage(
      source: ImageSource.camera,
      imageQuality: 80,
    );
    if (file == null) return;
    final bytes = await file.readAsBytes();
    setState(() {
      _selectedFileBytes = bytes;
      _selectedFileName = file.name;
    });
  }

  Future<void> _pickFromGallery() async {
    final file = await _imagePicker.pickImage(
      source: ImageSource.gallery,
      imageQuality: 80,
    );
    if (file == null) return;
    final bytes = await file.readAsBytes();
    setState(() {
      _selectedFileBytes = bytes;
      _selectedFileName = file.name;
    });
  }

  Future<void> _showFileSourcePicker() async {
    await showModalBottomSheet<void>(
      context: context,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) {
        return SafeArea(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              ListTile(
                leading: const Icon(Icons.camera_alt_outlined),
                title: const Text('Capture with camera'),
                onTap: () async {
                  Navigator.pop(context);
                  await _pickFromCamera();
                },
              ),
              ListTile(
                leading: const Icon(Icons.photo_library_outlined),
                title: const Text('Choose from gallery'),
                onTap: () async {
                  Navigator.pop(context);
                  await _pickFromGallery();
                },
              ),
              ListTile(
                leading: const Icon(Icons.attach_file_rounded),
                title: const Text('Browse files'),
                onTap: () async {
                  Navigator.pop(context);
                  await _pickFile();
                },
              ),
            ],
          ),
        );
      },
    );
  }

  Future<void> _pickExpiryDate() async {
    final now = DateTime.now();
    final picked = await showDatePicker(
      context: context,
      initialDate: now,
      firstDate: now,
      lastDate: DateTime(now.year + 10),
    );

    if (picked != null) {
      final month = picked.month.toString().padLeft(2, '0');
      final day = picked.day.toString().padLeft(2, '0');
      _expiryDateController.text = '${picked.year}-$month-$day';
      setState(() {});
    }
  }

  Future<void> _uploadDocument() async {
    final customerError = AppValidators.integerId(
        _customerIdController.text, 'documents.customer_id'.tr());
    final docTypeError = AppValidators.requiredField(
        _docTypeController.text, 'documents.document_type'.tr());

    if (customerError != null) {
      AppSnackBar.error(context, customerError);
      return;
    }

    if (docTypeError != null) {
      AppSnackBar.error(context, docTypeError);
      return;
    }

    if (_selectedFileBytes == null || _selectedFileName == null) {
      AppSnackBar.error(context, 'documents.choose_file_error'.tr());
      return;
    }

    setState(() {
      _uploading = true;
    });

    try {
      await _apiService.uploadDocument(
        customerId: int.parse(_customerIdController.text.trim()),
        docType: _docTypeController.text.trim(),
        fileBytes: _selectedFileBytes!,
        fileName: _selectedFileName!,
        expiryDate: _expiryDateController.text.trim(),
        notes: _notesController.text.trim(),
      );

      _notesController.clear();
      _expiryDateController.clear();

      setState(() {
        _selectedFileBytes = null;
        _selectedFileName = null;
        _documentsFuture = _loadDocuments();
      });

      if (!mounted) return;
      AppSnackBar.success(context, 'documents.upload_success'.tr());
    } catch (e) {
      if (!mounted) return;
      AppSnackBar.error(context, AppMessageHelper.extractErrorMessage(e));
    } finally {
      if (mounted) {
        setState(() {
          _uploading = false;
        });
      }
    }
  }

  @override
  void dispose() {
    _customerIdController.dispose();
    _docTypeController.dispose();
    _expiryDateController.dispose();
    _notesController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF6F7FB),
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        title: Text(
          'documents.title'.tr(),
          style: const TextStyle(
            color: Color(0xFF1C3566),
            fontWeight: FontWeight.w700,
            fontSize: 18,
          ),
        ),
      ),
      body: RefreshIndicator(
        onRefresh: _refreshDocuments,
        child: ListView(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
          children: [
            _uploadCard(),
            const SizedBox(height: 16),
            FutureBuilder<List<DocumentModel>>(
              future: _documentsFuture,
              builder: (context, snapshot) {
                if (snapshot.connectionState == ConnectionState.waiting) {
                  return Padding(
                    padding: const EdgeInsets.only(top: 40),
                    child:
                        AppLoadingIndicator(message: 'documents.loading'.tr()),
                  );
                }

                if (snapshot.hasError) {
                  return AppErrorState(
                    title: 'documents.failed_load'.tr(),
                    subtitle: 'documents.failed_load_subtitle'.tr(),
                    onRetry: _refreshDocuments,
                  );
                }

                final documents = snapshot.data ?? [];

                if (documents.isEmpty) {
                  return Padding(
                    padding: const EdgeInsets.only(top: 20),
                    child: AppEmptyState(
                      icon: Icons.description_outlined,
                      title: 'documents.empty_title'.tr(),
                      subtitle: 'documents.empty_subtitle'.tr(),
                    ),
                  );
                }

                return Column(
                  children: documents
                      .map(
                        (doc) => Padding(
                          padding: const EdgeInsets.only(bottom: 12),
                          child: _documentCard(doc),
                        ),
                      )
                      .toList(),
                );
              },
            ),
          ],
        ),
      ),
    );
  }

  Widget _uploadCard() {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [Color(0xFFFFFFFF), Color(0xFFF6FAFF)],
        ),
        border: Border.all(color: const Color(0xFFDCE5F3)),
        borderRadius: BorderRadius.circular(22),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF9DA8BE).withAlpha(28),
            blurRadius: 16,
            offset: const Offset(0, 9),
          ),
        ],
      ),
      child: Column(
        children: [
          _textField(
            controller: _customerIdController,
            label: 'documents.customer_id'.tr(),
            hint: '1',
            keyboardType: TextInputType.number,
          ),
          const SizedBox(height: 14),
          _textField(
            controller: _docTypeController,
            label: 'documents.document_type'.tr(),
            hint: 'LICENSE / PASSPORT / ID',
          ),
          const SizedBox(height: 14),
          InkWell(
            onTap: _pickExpiryDate,
            borderRadius: BorderRadius.circular(14),
            child: IgnorePointer(
              child: _textField(
                controller: _expiryDateController,
                label: 'documents.expiry_date'.tr(),
                hint: 'YYYY-MM-DD',
              ),
            ),
          ),
          const SizedBox(height: 14),
          _textField(
            controller: _notesController,
            label: 'documents.notes'.tr(),
            hint: 'common.optional'.tr(),
            maxLines: 3,
          ),
          const SizedBox(height: 14),
          InkWell(
            onTap: _showFileSourcePicker,
            borderRadius: BorderRadius.circular(14),
            child: Container(
              width: double.infinity,
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: const Color(0xFFD8DCE8)),
                color: const Color(0xFFF7F9FD),
              ),
              child: Row(
                children: [
                  const Icon(
                    Icons.attach_file_rounded,
                    color: Color(0xFF234E8C),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      _selectedFileName ?? 'documents.choose_file'.tr(),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.w500,
                        color: Color(0xFF162E60),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          AppPrimaryButton(
            label: 'documents.upload_document'.tr(),
            loading: _uploading,
            onPressed: _uploadDocument,
          ),
        ],
      ),
    );
  }

  Widget _documentCard(DocumentModel doc) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [Color(0xFFFFFFFF), Color(0xFFF6FAFF)],
        ),
        border: Border.all(color: const Color(0xFFDCE5F3)),
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF9DA8BE).withAlpha(28),
            blurRadius: 14,
            offset: const Offset(0, 9),
          ),
        ],
      ),
      child: Row(
        children: [
          Container(
            width: 42,
            height: 42,
            decoration: BoxDecoration(
              color: const Color(0xFF234E8C).withAlpha(31),
              shape: BoxShape.circle,
            ),
            child: const Icon(
              Icons.description_outlined,
              color: Color(0xFF234E8C),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  doc.docType,
                  style: const TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w700,
                    color: Color(0xFF162E60),
                  ),
                ),
                const SizedBox(height: 4),
                _statusPill(doc.status),
                const SizedBox(height: 4),
                Text(
                  doc.customerName.isNotEmpty
                      ? doc.customerName
                      : 'Customer ${doc.customer}',
                  style: const TextStyle(
                    fontSize: 12.5,
                    color: Color(0xFF6B7280),
                  ),
                ),
                if (doc.expiryDate.isNotEmpty) ...[
                  const SizedBox(height: 4),
                  Text(
                    'documents.expiry'.tr(args: [doc.expiryDate]),
                    style: const TextStyle(
                      fontSize: 12.5,
                      color: Color(0xFF6B7280),
                    ),
                  ),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _statusPill(String status) {
    final color = _statusColor(status);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: color.withAlpha(31),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Text(
        status.toUpperCase(),
        style: TextStyle(
          fontSize: 11,
          fontWeight: FontWeight.w700,
          color: color,
        ),
      ),
    );
  }

  Color _statusColor(String status) {
    switch (status.toUpperCase()) {
      case 'APPROVED':
      case 'VERIFIED':
        return const Color(0xFF179D57);
      case 'REJECTED':
        return const Color(0xFFD14848);
      case 'PENDING':
      default:
        return const Color(0xFFD28A17);
    }
  }

  Widget _textField({
    required TextEditingController controller,
    required String label,
    required String hint,
    TextInputType keyboardType = TextInputType.text,
    int maxLines = 1,
  }) {
    return TextField(
      controller: controller,
      keyboardType: keyboardType,
      maxLines: maxLines,
      decoration: InputDecoration(
        labelText: label,
        hintText: hint,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
        ),
      ),
    );
  }
}
