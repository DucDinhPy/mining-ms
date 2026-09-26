using System.ComponentModel.DataAnnotations;
using MineOps.Api.Models;

namespace MineOps.Api.DTOs.Cameras;

public class UpdateCameraRequest
{
    [Required]
    [MaxLength(150)]
    public string Name { get; set; } = string.Empty;

    [MaxLength(250)]
    public string? Location { get; set; }

    [Required]
    [MaxLength(2000)]
    public string StreamUrl { get; set; } = string.Empty;

    [EnumDataType(typeof(CameraStatus))]
    public CameraStatus Status { get; set; }

    [MaxLength(1000)]
    public string? Description { get; set; }
}