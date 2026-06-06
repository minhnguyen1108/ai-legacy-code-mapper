<?php

namespace App\Services;

use App\Repositories\ReportRepository;

class ReportService
{
    private $reportRepository;

    public function __construct(ReportRepository $reportRepository)
    {
        $this->reportRepository = $reportRepository;
    }

    public function createReport(array $payload)
    {
        $report = $this->reportRepository->insert($payload);
        $this->reportRepository->addHistory($report->id, 'created');
        return $report;
    }

    public function findReport($id)
    {
        return $this->reportRepository->find($id);
    }
}
