<?php

Route::group(['prefix' => 'api', 'middleware' => 'auth:api'], function () {
    Route::post('/report/create', 'ReportController@create')->name('report.create');
    Route::get('/report/{id}', 'ReportController@show')->name('report.show');
});
