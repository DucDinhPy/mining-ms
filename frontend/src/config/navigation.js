export const navigationGroups = [
  {
    label: 'Workspace',
    items: [
      {
        id: 'overview',
        label: 'Tổng quan',
        icon: 'dashboard',
        available: false,
        description: 'Tổng hợp hoạt động và chỉ số vận hành của toàn bộ công trường.',
      },
      {
        id: 'ppe',
        label: 'Phát hiện PPE',
        icon: 'shield',
        available: true,
        description: 'Giám sát thiết bị bảo hộ lao động bằng camera và AI theo thời gian thực.',
      },
    ],
  },
  {
    label: 'Vận hành',
    items: [
      {
        id: 'fleet',
        label: 'Giám sát đội xe',
        icon: 'truck',
        available: false,
        description: 'Theo dõi phương tiện, lộ trình và hiệu suất vận tải.',
      },
      {
        id: 'maintenance',
        label: 'Bảo trì dự báo',
        icon: 'maintenance',
        available: false,
        description: 'Theo dõi tình trạng và dự báo sự cố thiết bị.',
      },
      {
        id: 'environment',
        label: 'Môi trường',
        icon: 'environment',
        available: false,
        description: 'Giám sát bụi, nước, tiếng ồn và phát thải.',
      },
      {
        id: 'incidents',
        label: 'Quản lý sự cố',
        icon: 'incident',
        available: false,
        description: 'Ghi nhận, phân loại và theo dõi sự cố an toàn.',
      },
    ],
  },
  {
    label: 'Quản trị',
    items: [
      {
        id: 'reports',
        label: 'Báo cáo',
        icon: 'report',
        available: false,
        description: 'Báo cáo an toàn, hiệu suất và tuân thủ.',
      },
      {
        id: 'settings',
        label: 'Cài đặt',
        icon: 'settings',
        available: false,
        description: 'Quản lý camera, mô hình và cấu hình hệ thống.',
      },
    ],
  },
]
