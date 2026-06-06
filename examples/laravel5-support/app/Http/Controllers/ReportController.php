<?php

namespace App\Http\Controllers;

use App\Services\ReportService;

class ReportController extends Controller
{
    private $reportService;

    public function __construct(ReportService $reportService)
    {
        $this->reportService = $reportService;
    }

    public function create()
    {
        return $this->reportService->createReport(request()->all());
    }

    public function show($id)
    {
        return $this->reportService->findReport($id);
    }
}
