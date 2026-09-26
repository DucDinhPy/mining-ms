using Microsoft.AspNetCore.Mvc;
using MineOps.Api.DTOs.Cameras;
using MineOps.Api.DTOs.Common;
using MineOps.Api.Models;
using MineOps.Api.Repositories.Cameras;
using MineOps.Api.Mappings.Cameras;

namespace MineOps.Api.Controllers;


[ApiController]
[Route("api/cameras")]
public class CamerasController : ControllerBase
{
    private readonly ICameraRepository _cameraRepository;

    public CamerasController(ICameraRepository cameraRepository)
    {
        _cameraRepository = cameraRepository;
    }

    [HttpGet]
    public async Task<ActionResult<PagedResponse<CameraResponse>>> GetAll(
        [FromQuery] CameraGetAllRequest request,
        CancellationToken cancellationToken)
    {
        var (items, totalCount) =
            await _cameraRepository.GetAllAsync(
                request.Page,
                request.PageSize,
                cancellationToken);
        var responses = items
            .Select(camera => camera.ToResponse())
            .ToList();
        return Ok(new PagedResponse<CameraResponse>(
            responses,
            totalCount,
            request.Page,
            request.PageSize));
    }

    [HttpGet("{id:guid}")]
    public async Task<ActionResult<CameraResponse>> GetById(
        Guid id,
        CancellationToken cancellationToken)
    {
        var camera = await _cameraRepository.GetByIdAsync(
            id,
            cancellationToken);
        if (camera is null)
        {
            return NotFound();
        }
        return Ok(camera.ToResponse());
    }

    [HttpPost]
    public async Task<ActionResult<CameraResponse>> Create(
        [FromBody] CreateCameraRequest request,
        CancellationToken cancellationToken)
    {
        var camera = new Camera { 
            Name = request.Name.Trim(),
            Location = request.Location,
            StreamUrl = request.StreamUrl.Trim(),
            Status = request.Status,
            Description = request.Description
        };

        var createdCamera =
            await _cameraRepository.CreateAsync(
                camera,
                cancellationToken);

        var response = createdCamera.ToResponse();

        return Ok(response);


    }

}


//[ApiController]
//[Route("api/cameras")]
//public class CamerasController : ControllerBase
//{
//    private readonly ICameraRepository _cameraRepository;

//    public CamerasController(ICameraRepository cameraRepository)
//    {
//        _cameraRepository = cameraRepository;
//    }

//    [HttpGet]
//    public async Task<ActionResult<PagedResponse<CameraResponse>>> Search(
//        [FromQuery] CameraSearchRequest request,
//        CancellationToken cancellationToken)
//    {
//        var (items, totalCount) =
//            await _cameraRepository.SearchAsync(
//                request.Search,
//                request.Status,
//                request.Page,
//                request.PageSize,
//                cancellationToken);

//        var responses = items
//            .Select(ToResponse)
//            .ToList();

//        return Ok(new PagedResponse<CameraResponse>(
//            responses,
//            totalCount,
//            request.Page,
//            request.PageSize));
//    }

//    [HttpGet("{id:guid}")]
//    public async Task<ActionResult<CameraResponse>> GetById(
//        Guid id,
//        CancellationToken cancellationToken)
//    {
//        var camera = await _cameraRepository.GetByIdAsync(
//            id,
//            cancellationToken);

//        if (camera is null)
//        {
//            return NotFound();
//        }

//        return Ok(ToResponse(camera));
//    }

//    [HttpPost]
//    public async Task<ActionResult<CameraResponse>> Create(
//        [FromBody] CreateCameraRequest request,
//        CancellationToken cancellationToken)
//    {
//        var camera = new Camera
//        {
//            Name = request.Name.Trim(),
//            Location = NormalizeOptional(request.Location),
//            StreamUrl = request.StreamUrl.Trim(),
//            Status = request.Status,
//            Description = NormalizeOptional(request.Description)
//        };

//        var createdCamera =
//            await _cameraRepository.CreateAsync(
//                camera,
//                cancellationToken);

//        return CreatedAtAction(
//            nameof(GetById),
//            new { id = createdCamera.Id },
//            ToResponse(createdCamera));
//    }

//    [HttpPut("{id:guid}")]
//    public async Task<ActionResult<CameraResponse>> Update(
//        Guid id,
//        [FromBody] UpdateCameraRequest request,
//        CancellationToken cancellationToken)
//    {
//        var camera = new Camera
//        {
//            Id = id,
//            Name = request.Name.Trim(),
//            Location = NormalizeOptional(request.Location),
//            StreamUrl = request.StreamUrl.Trim(),
//            Status = request.Status,
//            Description = NormalizeOptional(request.Description)
//        };

//        var updated = await _cameraRepository.UpdateAsync(
//            camera,
//            cancellationToken);

//        if (!updated)
//        {
//            return NotFound();
//        }

//        var updatedCamera =
//            await _cameraRepository.GetByIdAsync(
//                id,
//                cancellationToken);

//        return Ok(ToResponse(updatedCamera!));
//    }

//    [HttpDelete("{id:guid}")]
//    public async Task<IActionResult> Delete(
//        Guid id,
//        CancellationToken cancellationToken)
//    {
//        var deleted = await _cameraRepository.DeleteAsync(
//            id,
//            cancellationToken);

//        if (!deleted)
//        {
//            return NotFound();
//        }

//        return NoContent();
//    }

//    private static CameraResponse ToResponse(Camera camera)
//    {
//        return new CameraResponse(
//            camera.Id,
//            camera.Name,
//            camera.Location,
//            camera.StreamUrl,
//            camera.Status,
//            camera.Description,
//            camera.CreatedAtUtc,
//            camera.UpdatedAtUtc);
//    }

//    private static string? NormalizeOptional(string? value)
//    {
//        return string.IsNullOrWhiteSpace(value)
//            ? null
//            : value.Trim();
//    }
//}