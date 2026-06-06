<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class ReportHistory extends Model
{
    protected $table = 'report_histories';
    protected $fillable = ['customer_report_id', 'action'];

    public function report()
    {
        return $this->belongsTo(CustomerReport::class);
    }
}
