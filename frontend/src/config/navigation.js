export const navigationGroups = [
  {
    label: 'Workspace',
    items: [
      {
        id: 'overview',
        label: 'Overview',
        icon: 'dashboard',
        available: false,
        description: 'A consolidated view of site activity and operational performance.',
      },
      {
        id: 'ppe',
        label: 'PPE Detection',
        icon: 'shield',
        available: true,
        description: 'Monitor personal protective equipment with cameras and real-time AI.',
      },
      {
        id: 'cameras',
        label: 'Cameras',
        icon: 'camera',
        available: true,
        description: 'Register and manage the video sources used by safety and AI modules.',
      },
    ],
  },
  {
    label: 'Operations',
    items: [
      {
        id: 'fleet',
        label: 'Fleet Monitoring',
        icon: 'truck',
        available: false,
        description: 'Track vehicles, routes, and haulage performance.',
      },
      {
        id: 'maintenance',
        label: 'Predictive Maintenance',
        icon: 'maintenance',
        available: false,
        description: 'Monitor equipment health and predict failures.',
      },
      {
        id: 'environment',
        label: 'Environment',
        icon: 'environment',
        available: false,
        description: 'Monitor dust, water, noise, and emissions.',
      },
      {
        id: 'incidents',
        label: 'Incident Management',
        icon: 'incident',
        available: false,
        description: 'Record, classify, and track safety incidents.',
      },
    ],
  },
  {
    label: 'Administration',
    items: [
      {
        id: 'reports',
        label: 'Reports',
        icon: 'report',
        available: false,
        description: 'Safety, performance, and compliance reporting.',
      },
      {
        id: 'settings',
        label: 'Settings',
        icon: 'settings',
        available: false,
        description: 'Manage cameras, AI models, and system configuration.',
      },
    ],
  },
]
