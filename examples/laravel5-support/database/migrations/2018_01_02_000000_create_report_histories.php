<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

class CreateReportHistories extends Migration
{
    public function up()
    {
        Schema::create('report_histories', function (Blueprint $table) {
            $table->increments('id');
            $table->unsignedInteger('customer_report_id');
            $table->string('action');
            $table->timestamps();
            $table->foreign('customer_report_id')
                ->references('id')
                ->on('customer_reports');
        });
    }
}
