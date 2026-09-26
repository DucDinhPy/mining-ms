using System.ComponentModel.DataAnnotations;
using MineOps.Api.Models;

namespace MineOps.Api.DTOs.Cameras;

public class CameraGetAllRequest
{

    [Range(1, int.MaxValue)]
    public int Page { get; set; } = 1;

    [Range(1, 100)]
    public int PageSize { get; set; } = 20;
}