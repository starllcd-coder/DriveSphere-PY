class DocumentModel {
  final int id;
  final int customer;
  final String customerName;
  final String docType;
  final String status;
  final String file;
  final String fileUrl;
  final String expiryDate;
  final String notes;
  final String createdAt;
  final String updatedAt;

  DocumentModel({
    required this.id,
    required this.customer,
    required this.customerName,
    required this.docType,
    required this.status,
    required this.file,
    required this.fileUrl,
    required this.expiryDate,
    required this.notes,
    required this.createdAt,
    required this.updatedAt,
  });

  factory DocumentModel.fromJson(Map<String, dynamic> json) {
    return DocumentModel(
      id: json['id'] ?? 0,
      customer: json['customer'] ?? 0,
      customerName: json['customer_name']?.toString() ?? '',
      docType: json['doc_type']?.toString() ?? '',
      status: json['status']?.toString() ?? 'PENDING',
      file: json['file']?.toString() ?? '',
      fileUrl: json['file_url']?.toString() ?? '',
      expiryDate: json['expiry_date']?.toString() ?? '',
      notes: json['notes']?.toString() ?? '',
      createdAt: json['created_at']?.toString() ?? '',
      updatedAt: json['updated_at']?.toString() ?? '',
    );
  }
}
